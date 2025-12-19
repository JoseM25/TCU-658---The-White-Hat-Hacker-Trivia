import random


class WildcardManager:
    # Charge constants
    MAX_CHARGES = 3
    STARTING_CHARGES = 1

    # Costs (all wildcards cost 1 charge)
    COST_REVEAL_LETTER = 1
    COST_FREEZE_TIMER = 1
    COST_DOUBLE_POINTS = 1

    # Rank thresholds (percentage of max_raw)
    A_RANK_THRESHOLD = 0.80
    S_RANK_THRESHOLD = 0.90

    # Anti-frustration: questions without earning a charge
    ANTI_FRUSTRATION_THRESHOLD = 3

    def __init__(self):
        # Shared charges across questions
        self._charges = self.STARTING_CHARGES

        # Track active effects for current question
        self._freeze_active = False
        self._double_points_stacks = 0

        # Track revealed positions to avoid re-revealing
        self._revealed_positions = set()

        # Track if any wildcard was used this question (for S Rank)
        self._wildcard_used_this_question = False

        # Track if double points was used (can't combine with others)
        self._double_points_used_this_question = False

        # Anti-frustration counter
        self._questions_without_charge = 0

    # Charge Management

    def get_charges(self):
        return self._charges

    def add_charge(self, amount=1):
        """Add charges, capped at MAX_CHARGES."""
        self._charges = min(self.MAX_CHARGES, self._charges + amount)
        return self._charges

    def spend_charge(self, amount):
        """Spend charges if available. Returns True if successful."""
        if self._charges >= amount:
            self._charges -= amount
            return True
        return False

    def can_afford(self, cost):
        """Check if player can afford a wildcard."""
        return self._charges >= cost

    def was_wildcard_used_this_question(self):
        """Check if any wildcard was used this question."""
        return self._wildcard_used_this_question

    def is_double_points_blocked(self):
        """Check if double points is blocked. Always returns False (no blocking)."""
        return False

    def are_other_wildcards_blocked(self):
        """Check if reveal/freeze are blocked. Always returns False (no blocking)."""
        return False

    # Freeze Wildcard

    def activate_freeze(self):
        """Activate freeze timer. Returns True if successful."""
        if not self.can_afford(self.COST_FREEZE_TIMER):
            return False
        if self._freeze_active:
            return False

        self.spend_charge(self.COST_FREEZE_TIMER)
        self._freeze_active = True
        self._wildcard_used_this_question = True
        return True

    def deactivate_freeze(self):
        self._freeze_active = False

    def is_timer_frozen(self):
        return self._freeze_active

    # Double Points Wildcard (stackable: x2, x4, x8, x16, ...)

    def activate_double_points(self):
        """Activate double points. Returns number of stacks if successful, 0 if failed."""
        if not self.can_afford(self.COST_DOUBLE_POINTS):
            return 0

        self.spend_charge(self.COST_DOUBLE_POINTS)
        self._double_points_stacks += 1
        self._wildcard_used_this_question = True
        self._double_points_used_this_question = True
        return self._double_points_stacks

    def get_double_points_stacks(self):
        return self._double_points_stacks

    def is_double_points_active(self):
        return self._double_points_stacks > 0

    def get_points_multiplier(self):
        # 2^n where n is the number of stacks (0 stacks = 1x, 1 stack = 2x, 2 stacks = 4x, etc.)
        return 2**self._double_points_stacks

    # Letter Reveal Wildcard

    def activate_reveal_letter(self, current_answer, correct_answer):
        """Reveal a random letter. Returns (position, letter) if successful, None if failed."""
        if not self.can_afford(self.COST_REVEAL_LETTER):
            return None

        result = self._get_random_unrevealed_position(current_answer, correct_answer)
        if result is None:
            return None

        self.spend_charge(self.COST_REVEAL_LETTER)
        self._wildcard_used_this_question = True
        return result

    def _get_random_unrevealed_position(self, current_answer, correct_answer):
        """Internal: find a random unrevealed position."""
        if not correct_answer:
            return None

        # Normalize inputs
        current_upper = current_answer.upper() if current_answer else ""
        correct_upper = correct_answer.upper()

        # Find positions where the letter doesn't match or isn't filled
        unrevealed_positions = []

        for i, correct_letter in enumerate(correct_upper):
            # Skip if this position was already revealed by wildcard
            if i in self._revealed_positions:
                continue

            # Check if position is unfilled or has wrong letter
            if i >= len(current_upper):
                # Position not yet typed
                unrevealed_positions.append((i, correct_letter))
            elif current_upper[i] != correct_letter:
                # Position has wrong letter
                unrevealed_positions.append((i, correct_letter))
            # If correct letter is already there, skip it

        if not unrevealed_positions:
            return None

        # Select random position
        position, letter = random.choice(unrevealed_positions)

        # Mark this position as revealed
        self._revealed_positions.add(position)

        return (position, letter)

    def get_random_unrevealed_position(self, current_answer, correct_answer):
        """Legacy method for compatibility. Use activate_reveal_letter instead."""
        return self._get_random_unrevealed_position(current_answer, correct_answer)

    def mark_position_revealed(self, position):
        self._revealed_positions.add(position)

    def get_revealed_positions(self):
        return self._revealed_positions.copy()

    # Charge Earning Logic

    def calculate_earned_charges(
        self, raw_points, max_raw, mistakes, was_skipped=False
    ):
        """
        Calculate charges earned after completing a question.
        Returns tuple (actual_charges_added, max_reached) where:
        - actual_charges_added: charges actually added to storage
        - max_reached: True if player would have earned charges but was at max
        """
        if was_skipped:
            # No charges on skip, but increment anti-frustration counter
            self._questions_without_charge += 1
            actual = self._check_anti_frustration()
            return (actual, False)

        if mistakes > 0:
            # No rank bonus with mistakes
            self._questions_without_charge += 1
            actual = self._check_anti_frustration()
            return (actual, False)

        # Perfect answer (0 mistakes)
        potential_charges = 0
        ratio = raw_points / max_raw if max_raw > 0 else 0

        # A Rank: correct with 0 mistakes AND raw >= 0.80 * maxRaw
        if ratio >= self.A_RANK_THRESHOLD:
            potential_charges += 1

        # S Rank: A Rank conditions + no wildcards used AND raw >= 0.90 * maxRaw
        if ratio >= self.S_RANK_THRESHOLD and not self._wildcard_used_this_question:
            potential_charges += 1

        if potential_charges > 0:
            self._questions_without_charge = 0
            old_charges = self._charges
            self.add_charge(potential_charges)
            actual_added = self._charges - old_charges
            max_reached = actual_added < potential_charges
            return (actual_added, max_reached)
        else:
            self._questions_without_charge += 1
            actual = self._check_anti_frustration()
            return (actual, False)

    def _check_anti_frustration(self):
        """Check and apply anti-frustration bonus if needed."""
        if self._questions_without_charge >= self.ANTI_FRUSTRATION_THRESHOLD:
            self._questions_without_charge = 0
            self.add_charge(1)
            return 1
        return 0

    # Reset / State Management

    def reset_for_new_question(self):
        """Reset per-question state, keep charges."""
        self._freeze_active = False
        self._double_points_stacks = 0
        self._revealed_positions.clear()
        self._wildcard_used_this_question = False
        self._double_points_used_this_question = False

    def reset_game(self):
        """Full reset for new game."""
        self._charges = self.STARTING_CHARGES
        self._questions_without_charge = 0
        self.reset_for_new_question()

    def get_active_effects(self):
        return {
            "freeze": self._freeze_active,
            "double_points_stacks": self._double_points_stacks,
            "points_multiplier": self.get_points_multiplier(),
            "revealed_count": len(self._revealed_positions),
            "charges": self._charges,
            "wildcard_used": self._wildcard_used_this_question,
            "questions_without_charge": self._questions_without_charge,
        }
