class QuestionResult:
    def __init__(
        self,
        points_earned=0,
        was_correct=False,
        was_skipped=False,
        mistakes=0,
        time_seconds=0,
    ):
        self.points_earned = points_earned
        self.was_correct = was_correct
        self.was_skipped = was_skipped
        self.mistakes = mistakes
        self.time_seconds = time_seconds


class ScoringSystem:
    # Valores de referencia para escalado
    REFERENCE_QUESTIONS = 15
    REFERENCE_BASE = 350

    # Límites para puntos base
    BASE_MIN = 200
    BASE_MAX = 700

    # Constantes del temporizador
    GRACE_PERIOD_SECONDS = 5

    # Umbrales de bonificación por velocidad (en segundos después del período de gracia)
    SPEED_TIER_1_MAX = 40  # Rápido: 1.50x
    SPEED_TIER_2_MAX = 80  # Medio: 1.50 a 1.00
    SPEED_TIER_3_MAX = 160  # Lento: 1.00 a 0.50

    # Valores de multiplicador
    MAX_TIME_MULTIPLIER = 1.50
    MID_TIME_MULTIPLIER = 1.00
    MIN_TIME_MULTIPLIER = 0.50

    # Penalización
    MISTAKE_PENALTY_FACTOR = 0.10  # 10% de BASE por error

    # Streak constants
    STREAK_BONUS_PER_LEVEL = 0.05  # 5% bonus per streak level
    STREAK_MAX_LEVEL = 10  # Cap at 10 (1.50x max)

    def __init__(self, total_questions):
        self.total_questions = max(1, total_questions)
        self.base_points = self._calculate_base_points()
        self.max_raw_per_question = self.base_points * self.MAX_TIME_MULTIPLIER
        self.penalty_per_mistake = round(self.base_points * self.MISTAKE_PENALTY_FACTOR)

        # Estado de la sesión
        self.total_score = 0
        self.questions_answered = 0
        self.total_raw_points = 0

        # Streak tracking
        self.clean_streak = 0

    def get_session_max_raw(self):
        return self.total_questions * self.max_raw_per_question

    def get_mastery_percentage(self):
        session_max_raw = self.get_session_max_raw()
        if session_max_raw <= 0:
            return 0.0
        mastery_pct = (self.total_raw_points / session_max_raw) * 100.0
        return max(0.0, min(100.0, mastery_pct))

    def get_knowledge_level(self, mastery_pct=None):
        pct = self.get_mastery_percentage() if mastery_pct is None else mastery_pct

        if pct < 40:
            return "Beginner"
        if pct < 55:
            return "Student"
        if pct < 70:
            return "Professional"
        if pct < 85:
            return "Expert"
        return "Master"

    def _calculate_base_points(self):
        scaled = round(
            self.REFERENCE_BASE * self.REFERENCE_QUESTIONS / self.total_questions
        )
        return max(self.BASE_MIN, min(self.BASE_MAX, scaled))

    def get_effective_time(self, raw_seconds):
        return max(0, raw_seconds - self.GRACE_PERIOD_SECONDS)

    def calculate_time_multiplier(self, effective_seconds):
        t = effective_seconds

        if t <= self.SPEED_TIER_1_MAX:
            return self.MAX_TIME_MULTIPLIER

        if t <= self.SPEED_TIER_2_MAX:
            progress = (t - self.SPEED_TIER_1_MAX) / (
                self.SPEED_TIER_2_MAX - self.SPEED_TIER_1_MAX
            )
            return self.MAX_TIME_MULTIPLIER - progress * (
                self.MAX_TIME_MULTIPLIER - self.MID_TIME_MULTIPLIER
            )

        if t <= self.SPEED_TIER_3_MAX:
            progress = (t - self.SPEED_TIER_2_MAX) / (
                self.SPEED_TIER_3_MAX - self.SPEED_TIER_2_MAX
            )
            return self.MID_TIME_MULTIPLIER - progress * (
                self.MID_TIME_MULTIPLIER - self.MIN_TIME_MULTIPLIER
            )

        return self.MIN_TIME_MULTIPLIER

    def calculate_raw_points(self, effective_seconds):
        time_mult = self.calculate_time_multiplier(effective_seconds)
        return round(self.base_points * time_mult)

    def calculate_score(self, time_seconds, mistakes):
        effective_time = self.get_effective_time(time_seconds)
        raw_points = self.calculate_raw_points(effective_time)

        penalty = mistakes * self.penalty_per_mistake
        score = max(0, raw_points - penalty)

        return score

    def calculate_streak_multiplier(self):
        capped_streak = min(self.clean_streak, self.STREAK_MAX_LEVEL)
        return 1.0 + (self.STREAK_BONUS_PER_LEVEL * capped_streak)

    def _log_scoring_details(
        self,
        action,
        raw_points,
        score_before_streak,
        streak_mult,
        final_points,
        mistakes,
        time_seconds,
    ):
        print(f"\n{'='*50}")
        print(f"[SCORING] Action: {action}")
        print(f"[SCORING] Time: {time_seconds}s | Mistakes: {mistakes}")
        print(f"[SCORING] Raw Points: {raw_points}")
        print(f"[SCORING] Score Before Streak: {score_before_streak}")
        print(
            f"[SCORING] Clean Streak: {self.clean_streak} | Streak Multiplier: {streak_mult:.2f}x"
        )
        print(f"[SCORING] Final Points: {final_points}")
        print(f"[SCORING] Total Score: {self.total_score}")
        print(f"{'='*50}\n")

    def process_correct_answer(self, time_seconds, mistakes):
        effective_time = self.get_effective_time(time_seconds)
        raw_points = self.calculate_raw_points(effective_time)
        score_before_streak = self.calculate_score(time_seconds, mistakes)

        # Streak logic: increase only if correct with 0 mistakes
        if mistakes == 0:
            self.clean_streak += 1
        else:
            self.clean_streak = 0

        # Apply streak multiplier
        streak_mult = self.calculate_streak_multiplier()
        final_points = round(score_before_streak * streak_mult)

        self.total_score += final_points
        self.questions_answered += 1
        self.total_raw_points += raw_points

        # Log scoring details
        self._log_scoring_details(
            action="CORRECT",
            raw_points=raw_points,
            score_before_streak=score_before_streak,
            streak_mult=streak_mult,
            final_points=final_points,
            mistakes=mistakes,
            time_seconds=time_seconds,
        )

        return QuestionResult(
            points_earned=final_points,
            was_correct=True,
            was_skipped=False,
            mistakes=mistakes,
            time_seconds=time_seconds,
        )

    def process_skip(self):
        # Streak resets on skip
        previous_streak = self.clean_streak
        self.clean_streak = 0

        self.questions_answered += 1

        # Log skip action
        print(f"\n{'='*50}")
        print("[SCORING] Action: SKIP")
        print(f"[SCORING] Previous Streak: {previous_streak} -> Reset to 0")
        print("[SCORING] Points Earned: 0")
        print(f"[SCORING] Total Score: {self.total_score}")
        print(f"{'='*50}\n")

        return QuestionResult(
            points_earned=0,
            was_correct=False,
            was_skipped=True,
            mistakes=0,
            time_seconds=0,
        )

    def process_wrong_answer(self):
        print("[SCORING] Wrong answer! Streak will reset on next question.")

    def get_session_stats(self):
        mastery_pct = self.get_mastery_percentage()
        session_max_raw = self.get_session_max_raw()
        return {
            "total_score": self.total_score,
            "total_raw_points": self.total_raw_points,
            "session_max_raw": session_max_raw,
            "mastery_pct": mastery_pct,
            "knowledge_level": self.get_knowledge_level(mastery_pct),
            "questions_answered": self.questions_answered,
            "total_questions": self.total_questions,
            "base_points": self.base_points,
            "penalty_per_mistake": self.penalty_per_mistake,
            "grace_period_seconds": self.GRACE_PERIOD_SECONDS,
            "max_possible_per_question": round(self.max_raw_per_question),
            "clean_streak": self.clean_streak,
            "streak_multiplier": self.calculate_streak_multiplier(),
        }
