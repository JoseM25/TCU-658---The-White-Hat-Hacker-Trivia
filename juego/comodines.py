import random


class WildcardManager:
    # Constantes de cargas
    MAX_CHARGES = 3
    STARTING_CHARGES = 1

    # Costos (todos los comodines cuestan 1 carga)
    COST_REVEAL_LETTER = 1
    COST_FREEZE_TIMER = 1
    COST_DOUBLE_POINTS = 1

    # Umbrales de rango (porcentaje de max_raw)
    A_RANK_THRESHOLD = 0.80
    S_RANK_THRESHOLD = 0.90

    # Anti-frustración: preguntas sin ganar una carga
    ANTI_FRUSTRATION_THRESHOLD = 3

    def __init__(self):
        # Cargas compartidas entre preguntas
        self.charges = self.STARTING_CHARGES

        # Seguimiento de efectos activos para pregunta actual
        self.freeze_active = False
        self.double_points_stacks = 0

        # Seguimiento de posiciones reveladas para evitar revelar de nuevo
        self.revealed_positions = set()

        # Seguimiento si se usó algún comodín esta pregunta (para Rango S)
        self.wildcard_used_this_question = False

        # Seguimiento si se usó puntos dobles (no se puede combinar con otros)
        self.double_points_used_this_question = False

        # Contador anti-frustración
        self.questions_without_charge = 0

    # Manejo de Cargas

    def get_charges(self):
        return self.charges

    def add_charge(self, amount=1):
        self.charges = min(self.MAX_CHARGES, self.charges + amount)
        return self.charges

    def spend_charge(self, amount):
        if self.charges >= amount:
            self.charges -= amount
            return True
        return False

    def can_afford(self, cost):
        return self.charges >= cost

    def was_wildcard_used_this_question(self):
        return self.wildcard_used_this_question

    def is_double_points_blocked(self):
        return False

    def are_other_wildcards_blocked(self):
        return False

    # Comodín de Congelar

    def activate_freeze(self):
        if not self.can_afford(self.COST_FREEZE_TIMER):
            return False
        if self.freeze_active:
            return False

        self.spend_charge(self.COST_FREEZE_TIMER)
        self.freeze_active = True
        self.wildcard_used_this_question = True
        return True

    def deactivate_freeze(self):
        self.freeze_active = False

    def is_timer_frozen(self):
        return self.freeze_active

    # Comodín de Puntos Dobles (acumulable: x2, x4, x8, x16, ...)

    def activate_double_points(self):
        if not self.can_afford(self.COST_DOUBLE_POINTS):
            return 0

        self.spend_charge(self.COST_DOUBLE_POINTS)
        self.double_points_stacks += 1
        self.wildcard_used_this_question = True
        self.double_points_used_this_question = True
        return self.double_points_stacks

    def get_double_points_stacks(self):
        return self.double_points_stacks

    def is_double_points_active(self):
        return self.double_points_stacks > 0

    def get_points_multiplier(self):
        # 2^n donde n es el número de acumulaciones (0 = 1x, 1 = 2x, 2 = 4x, etc.)
        return 2**self.double_points_stacks

    # Comodín de Revelar Letra

    def activate_reveal_letter(self, current_answer, correct_answer):
        if not self.can_afford(self.COST_REVEAL_LETTER):
            return None

        result = self.compute_random_unrevealed_position(current_answer, correct_answer)
        if result is None:
            return None

        self.spend_charge(self.COST_REVEAL_LETTER)
        self.wildcard_used_this_question = True
        return result

    def compute_random_unrevealed_position(self, current_answer, correct_answer):
        if not correct_answer:
            return None

        # Normalizar entradas
        current_upper = current_answer.upper() if current_answer else ""
        correct_upper = correct_answer.upper()

        # Encontrar posiciones donde la letra no coincide o no está llena
        unrevealed_positions = []

        for i, correct_letter in enumerate(correct_upper):
            # Saltar si esta posición ya fue revelada por comodín
            if i in self.revealed_positions:
                continue

            # Verificar si la posición está vacía o tiene letra incorrecta
            if i >= len(current_upper):
                # Posición aún no escrita
                unrevealed_positions.append((i, correct_letter))
            elif current_upper[i] != correct_letter:
                # Posición tiene letra incorrecta
                unrevealed_positions.append((i, correct_letter))
            # Si la letra correcta ya está, saltar

        if not unrevealed_positions:
            return None

        # Seleccionar posición aleatoria
        position, letter = random.choice(unrevealed_positions)

        # Marcar esta posición como revelada
        self.revealed_positions.add(position)

        return (position, letter)

    def get_random_unrevealed_position(self, current_answer, correct_answer):
        return self.compute_random_unrevealed_position(current_answer, correct_answer)

    def mark_position_revealed(self, position):
        self.revealed_positions.add(position)

    def get_revealed_positions(self):
        return self.revealed_positions.copy()

    # Lógica de Ganancia de Cargas

    def calculate_earned_charges(
        self, raw_points, max_raw, mistakes, was_skipped=False
    ):
        if was_skipped:
            # Sin cargas al saltar, pero incrementar contador anti-frustración
            self.questions_without_charge += 1
            actual = self.check_anti_frustration()
            return (actual, False)

        if mistakes > 0:
            # Sin bonificación de rango con errores
            self.questions_without_charge += 1
            actual = self.check_anti_frustration()
            return (actual, False)

        # Respuesta perfecta (0 errores)
        potential_charges = 0
        ratio = raw_points / max_raw if max_raw > 0 else 0

        # Rango A: correcto con 0 errores Y raw >= 0.80 * maxRaw
        if ratio >= self.A_RANK_THRESHOLD:
            potential_charges += 1

        # Rango S: condiciones de Rango A + sin comodines usados Y raw >= 0.90 * maxRaw
        if ratio >= self.S_RANK_THRESHOLD and not self.wildcard_used_this_question:
            potential_charges += 1

        if potential_charges > 0:
            self.questions_without_charge = 0
            old_charges = self.charges
            self.add_charge(potential_charges)
            actual_added = self.charges - old_charges
            max_reached = actual_added < potential_charges
            return (actual_added, max_reached)
        else:
            self.questions_without_charge += 1
            actual = self.check_anti_frustration()
            return (actual, False)

    def check_anti_frustration(self):
        if self.questions_without_charge >= self.ANTI_FRUSTRATION_THRESHOLD:
            self.questions_without_charge = 0
            self.add_charge(1)
            return 1
        return 0

    # Reinicio / Manejo de Estado

    def reset_for_new_question(self):
        self.freeze_active = False
        self.double_points_stacks = 0
        self.revealed_positions.clear()
        self.wildcard_used_this_question = False
        self.double_points_used_this_question = False

    def reset_game(self):
        self.charges = self.STARTING_CHARGES
        self.questions_without_charge = 0
        self.reset_for_new_question()

    def get_active_effects(self):
        return {
            "freeze": self.freeze_active,
            "double_points_stacks": self.double_points_stacks,
            "points_multiplier": self.get_points_multiplier(),
            "revealed_count": len(self.revealed_positions),
            "charges": self.charges,
            "wildcard_used": self.wildcard_used_this_question,
            "questions_without_charge": self.questions_without_charge,
        }
