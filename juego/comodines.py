import random


class WildcardManager:

    def __init__(self):
        # Track active effects for current question
        self._freeze_active = False
        self._double_points_stacks = (
            0  # Number of times X2 was pressed (multiplier = 2^n)
        )

        # Track revealed positions to avoid re-revealing
        self._revealed_positions = set()

    # Freeze Wildcard

    def activate_freeze(self):
        self._freeze_active = True
        return True

    def deactivate_freeze(self):
        self._freeze_active = False

    def is_timer_frozen(self):
        return self._freeze_active

    # Double Points Wildcard (stackable: x2, x4, x8, x16, ...)

    def activate_double_points(self):
        self._double_points_stacks += 1
        return self._double_points_stacks

    def get_double_points_stacks(self):
        return self._double_points_stacks

    def is_double_points_active(self):
        return self._double_points_stacks > 0

    def get_points_multiplier(self):
        # 2^n where n is the number of stacks (0 stacks = 1x, 1 stack = 2x, 2 stacks = 4x, etc.)
        return 2**self._double_points_stacks

    # Letter Reveal Wildcard

    def get_random_unrevealed_position(self, current_answer, correct_answer):
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

    def mark_position_revealed(self, position):
        self._revealed_positions.add(position)

    def get_revealed_positions(self):
        return self._revealed_positions.copy()

    # Reset / State Management

    def reset_for_new_question(self):
        self._freeze_active = False
        self._double_points_stacks = 0
        self._revealed_positions.clear()

    def get_active_effects(self):
        return {
            "freeze": self._freeze_active,
            "double_points_stacks": self._double_points_stacks,
            "points_multiplier": self.get_points_multiplier(),
            "revealed_count": len(self._revealed_positions),
        }
