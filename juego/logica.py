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

    def __init__(self, total_questions):
        self.total_questions = max(1, total_questions)
        self.base_points = self._calculate_base_points()
        self.max_raw_per_question = self.base_points * self.MAX_TIME_MULTIPLIER
        self.penalty_per_mistake = round(self.base_points * self.MISTAKE_PENALTY_FACTOR)

        # Estado de la sesión
        self.total_score = 0
        self.questions_answered = 0
        self.total_raw_points = 0

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

    def process_correct_answer(self, time_seconds, mistakes):
        effective_time = self.get_effective_time(time_seconds)
        raw_points = self.calculate_raw_points(effective_time)
        points = self.calculate_score(time_seconds, mistakes)

        self.total_score += points
        self.questions_answered += 1
        self.total_raw_points += raw_points

        return QuestionResult(
            points_earned=points,
            was_correct=True,
            was_skipped=False,
            mistakes=mistakes,
            time_seconds=time_seconds,
        )

    def process_skip(self):
        self.questions_answered += 1

        return QuestionResult(
            points_earned=0,
            was_correct=False,
            was_skipped=True,
            mistakes=0,
            time_seconds=0,
        )

    def process_wrong_answer(self):
        pass

    def get_session_stats(self):
        return {
            "total_score": self.total_score,
            "questions_answered": self.questions_answered,
            "total_questions": self.total_questions,
            "base_points": self.base_points,
            "max_possible_per_question": round(self.max_raw_per_question),
        }
