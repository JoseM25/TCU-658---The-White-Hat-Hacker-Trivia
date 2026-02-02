import random
import tkinter as tk

import customtkinter as ctk
from PIL import Image

from juego.pantalla_juego_base import GameScreenBase
from juego.pantalla_juego_modales import (
    GameCompletionModal,
    QuestionSummaryModal,
    SkipConfirmationModal,
)


class GameScreenLogic(GameScreenBase):

    def __init__(
        self, parent, on_return_callback=None, tts_service=None, sfx_service=None
    ):
        # Pre-inicializar atributos antes de llamar al constructor padre
        # para satisfacer al linter (estos se re-inicializan en el padre)
        self.current_question = None
        self.current_answer = ""
        self.current_image = None
        self.processing_correct_answer = False
        self.question_timer = 0
        self.question_mistakes = 0
        self.audio_enabled = True
        self.questions_answered = 0
        self.score = 0
        self.stored_modal_data = None
        self.game_completed = False
        self.viewing_history_index = -1
        self.question_history = []
        self.awaiting_modal_decision = False
        self.feedback_animation_job = None
        self.timer_running = False
        self.timer_job = None
        self.skip_modal = None
        self.completion_modal = None
        self.summary_modal = None
        self.cached_original_image = None
        self.cached_image_path = None  # Track which image path is cached

        super().__init__(parent, on_return_callback, tts_service, sfx_service)

    def on_wildcard_x2(self):
        if (
            not self.current_question
            or self.awaiting_modal_decision
            or self.viewing_history_index >= 0
        ):
            return

        stacks = self.wildcard_manager.activate_double_points()
        if stacks > 0:
            multiplier = self.wildcard_manager.get_points_multiplier()
            self.wildcard_x2_btn.configure(text=f"X{multiplier}")
            self.apply_double_points_visuals(multiplier)
            self.update_wildcard_buttons_state()
            if self.sfx:
                self.sfx.play("points", stop_previous=True)

    def on_wildcard_hint(self):
        if (
            not self.current_question
            or self.awaiting_modal_decision
            or self.viewing_history_index >= 0
        ):
            return

        title = self.current_question.get("title", "").replace(" ", "").upper()
        result = self.wildcard_manager.activate_reveal_letter(
            self.current_answer, title
        )
        if result is None:
            return

        pos, letter = result
        ans = list(self.current_answer.upper())
        while len(ans) <= pos:
            ans.append(" ")
        ans[pos] = letter
        self.current_answer = "".join(ans).rstrip()
        self.update_answer_boxes_with_reveal(pos)
        self.update_wildcard_buttons_state()
        if self.sfx:
            self.sfx.play("reveal", stop_previous=True)

    def on_wildcard_freeze(self):
        if (
            not self.current_question
            or self.awaiting_modal_decision
            or self.viewing_history_index >= 0
        ):
            return

        if not self.wildcard_manager.activate_freeze():
            return

        self.apply_freeze_timer_visuals()
        self.stop_timer()
        self.update_wildcard_buttons_state()
        if self.sfx:
            self.sfx.play("freeze", stop_previous=True)

    def load_random_question(self):
        self.tts.stop()
        self.hide_feedback()
        self.processing_correct_answer = False
        self.wildcard_manager.reset_for_new_question()
        self.update_wildcard_buttons_state()
        self.reset_timer_visuals()
        self.reset_double_points_visuals()

        # Limpiar caché de imagen
        self.cached_original_image = None
        self.cached_image_path = None

        if not self.questions:
            self.set_definition_text("No questions available!")
            return

        if not self.available_questions:
            self.handle_game_completion()
            return

        self.current_question = random.choice(self.available_questions)
        self.available_questions.remove(self.current_question)
        self.current_answer = ""
        self.question_timer = 0
        self.question_mistakes = 0
        self.timer_label.configure(text="00:00")

        definition = self.current_question.get("definition", "No definition")
        self.set_definition_text(definition)
        self.create_answer_boxes(
            len(self.current_question.get("title", "").replace(" ", ""))
        )
        self.load_question_image()

        if self.audio_enabled and definition and definition != "No definition":
            self.tts.speak(definition)

    def load_question_image(self):
        if not self.current_question:
            return

        image_path = self.current_question.get("image", "")
        if not image_path:
            self.image_label.configure(image=None, text="No Image")
            self.current_image = None
            self.cached_original_image = None
            self.cached_image_path = None
            return

        try:
            # Inicializar caché si no existe
            if not hasattr(self, "cached_original_image"):
                self.cached_original_image = None
            if not hasattr(self, "cached_image_path"):
                self.cached_image_path = None

            # Cargar imagen solo si no está en caché O si la ruta cambió
            if (
                self.cached_original_image is None
                or self.cached_image_path != image_path
            ):
                resolved_path = None
                if self.image_handler:
                    resolved_path = self.image_handler.resolve_image_path(image_path)

                if resolved_path and resolved_path.exists():
                    with Image.open(resolved_path) as img:
                        # Guardamos copia RGBA en memoria
                        self.cached_original_image = img.convert("RGBA").copy()
                        self.cached_image_path = image_path
                else:
                    self.image_label.configure(image=None, text="Image not found")
                    self.current_image = None
                    self.cached_original_image = None
                    self.cached_image_path = None
                    return

            # Si tenemos imagen en caché, redimensionar
            if self.cached_original_image:
                max_sz = self.get_scaled_image_size()
                w, h = self.cached_original_image.size
                if w > 0 and h > 0:
                    sc = min(max_sz / w, max_sz / h)

                    self.current_image = ctk.CTkImage(
                        light_image=self.cached_original_image,
                        dark_image=self.cached_original_image,
                        size=(int(w * sc), int(h * sc)),
                    )
                    self.image_label.configure(image=self.current_image, text="")
            else:
                self.image_label.configure(image=None, text="Image Error")
                self.current_image = None

        except (FileNotFoundError, OSError, ValueError) as e:
            print(f"Error loading image: {e}")
            self.image_label.configure(image=None, text="Error loading image")
            self.current_image = None

    def reload_question_image(self):
        self.load_question_image()

    def on_key_press(self, key):
        if not self.current_question or self.awaiting_modal_decision:
            return

        title = self.current_question.get("title", "").replace(" ", "")
        max_len = len(title)
        revealed = self.wildcard_manager.get_revealed_positions()

        # Rellenar la respuesta actual hasta max_len con espacios para preservar posiciones
        ans = list(self.current_answer.ljust(max_len))

        if key == "⌫":
            # Encontrar la última posición no revelada con contenido y limpiarla
            for i in range(max_len - 1, -1, -1):
                if i in revealed:
                    continue
                if ans[i].strip():
                    ans[i] = " "
                    break
        else:
            # Encontrar la primera posición vacía no revelada y llenarla
            for i in range(max_len):
                if i in revealed:
                    continue
                if not ans[i].strip():
                    ans[i] = key
                    break

        # Recortar espacios finales, pero nunca por debajo de la posición revelada más alta + 1
        min_len = (max(revealed) + 1) if revealed else 0
        while len(ans) > min_len and not ans[-1].strip():
            ans.pop()

        self.current_answer = "".join(ans)
        self.update_answer_boxes()

    def update_answer_boxes(self):
        revealed = self.wildcard_manager.get_revealed_positions()
        for i, box in enumerate(self.answer_box_labels):
            has = i < len(self.current_answer) and self.current_answer[i].strip()
            if has:
                box.configure(
                    text=self.current_answer[i],
                    fg_color=(
                        self.COLORS["success_green"]
                        if i in revealed
                        else self.COLORS["answer_box_filled"]
                    ),
                )
            else:
                box.configure(text="", fg_color=self.COLORS["answer_box_empty"])

    def update_answer_boxes_with_reveal(self, pos):
        self.update_answer_boxes()
        if pos < len(self.answer_box_labels):
            self.animate_reveal_flash(pos)

    def animate_reveal_flash(self, pos):
        if pos >= len(self.answer_box_labels):
            return
        box = self.answer_box_labels[pos]
        try:
            box.configure(fg_color="#00FFE5")
        except tk.TclError:
            pass
        self.parent.after(
            150,
            lambda: self.safe_configure(box, fg_color=self.COLORS["success_green"]),
        )

    def safe_configure(self, widget, **kw):
        try:
            widget.configure(**kw)
        except tk.TclError:
            pass

    def toggle_audio(self):
        self.audio_enabled = not self.audio_enabled
        self.update_audio_button_icon()
        if self.sfx:
            self.sfx.set_muted(not self.audio_enabled)
        if self.audio_enabled and self.current_question:
            defn = self.current_question.get("definition", "").strip()
            if defn:
                self.tts.speak(defn)
        else:
            self.tts.stop()

    def on_skip(self):
        if (
            not self.current_question
            or self.processing_correct_answer
            or self.awaiting_modal_decision
            or self.viewing_history_index >= 0
        ):
            return

        if self.skip_modal is None:
            self.skip_modal = SkipConfirmationModal(
                self.parent,
                self.do_skip,
                self.get_current_scale(),
            )
        self.skip_modal.show()

    def do_skip(self):
        if not self.current_question:
            return

        self.stop_timer()
        self.tts.stop()
        title = self.current_question.get("title", "")

        if self.scoring_system:
            self.scoring_system.process_skip(mistakes=self.question_mistakes)
            self.questions_answered = self.scoring_system.questions_answered
            self.score = self.scoring_system.total_score
        else:
            self.questions_answered += 1

        # Calcular cargas por saltar (para seguimiento anti-frustración)
        charges_earned, charges_max_reached = (
            self.wildcard_manager.calculate_earned_charges(0, 1, 0, was_skipped=True)
        )

        self.score_label.configure(text=str(self.score))
        streak = self.scoring_system.clean_streak if self.scoring_system else 0
        streak_mult = (
            self.scoring_system.calculate_streak_multiplier()
            if self.scoring_system
            else 1.0
        )

        self.stored_modal_data = {
            "correct_word": title,
            "time_taken": self.question_timer,
            "points_awarded": 0,
            "total_score": self.score,
            "question": self.current_question,
            "answer": self.current_answer,
            "was_skipped": True,
            "multiplier": 1,
            "streak": streak,
            "streak_multiplier": streak_mult,
            "charges_earned": charges_earned,
            "charges_max_reached": charges_max_reached,
        }
        self.show_feedback(skipped=True)
        self.show_summary_modal_for_state(self.stored_modal_data)

    def handle_game_completion(self):
        if self.game_completed:
            return

        self.game_completed = True
        self.stop_timer()
        self.tts.stop()
        self.current_question = None
        self.set_definition_text("Game Complete!")

        stats = self.scoring_system.get_session_stats() if self.scoring_system else None
        if self.sfx:
            self.sfx.play("win", stop_previous=True)
        self.completion_modal = GameCompletionModal(
            self.parent,
            self.score,
            len(self.questions),
            stats,
            self.on_completion_previous,
            bool(self.question_history),
            self.return_to_menu,
            self.get_current_scale(),
        )
        self.completion_modal.show()

    def on_check(self):
        if not self.current_question:
            return

        if self.viewing_history_index >= 0:
            self.show_summary_modal_for_state(
                self.question_history[self.viewing_history_index],
                review_mode=self.game_completed,
            )
            return

        if self.awaiting_modal_decision and self.stored_modal_data:
            self.show_summary_modal_for_state(self.stored_modal_data)
            return

        if self.processing_correct_answer:
            return

        title = self.current_question.get("title", "")
        clean = title.replace(" ", "")
        targetlen = len(clean)
        ans = self.current_answer.ljust(targetlen)
        full = True
        for i in range(targetlen):
            if not ans[i].strip():
                full = False
                break
        if not full:
            if self.feedback_animation_job:
                try:
                    self.parent.after_cancel(self.feedback_animation_job)
                except tk.TclError:
                    pass
                self.feedback_animation_job = None
            txt = "Fill all spaces"
            clr = self.COLORS.get("warning_yellow", "#FFC553")
            self.feedback_label.configure(text=txt, text_color=clr)
            self.animate_feedback(0, clr)
            return
        if self.current_answer.upper() == clean.upper():
            self.processing_correct_answer = True
            self.stop_timer()
            self.tts.stop()
            self.show_feedback(correct=True)
            if self.sfx:
                self.sfx.play("correct", stop_previous=True)

            pts = 0
            raw_pts = 0
            max_raw = 0
            mult = self.wildcard_manager.get_points_multiplier()

            if self.scoring_system:
                effective_time = self.scoring_system.get_effective_time(
                    self.question_timer
                )
                raw_pts = self.scoring_system.calculate_raw_points(effective_time)
                max_raw = self.scoring_system.max_raw_per_question

                res = self.scoring_system.process_correct_answer(
                    time_seconds=self.question_timer,
                    mistakes=self.question_mistakes,
                )
                pts = res.points_earned
                if mult > 1:
                    self.scoring_system.total_score += pts * (mult - 1)
                    pts *= mult
                self.score = self.scoring_system.total_score
                self.questions_answered = self.scoring_system.questions_answered
            else:
                pts = 100 * mult
                raw_pts = 100
                max_raw = 150
                self.score += pts
                self.questions_answered += 1

            # Calcular cargas ganadas
            charges_earned, charges_max_reached = (
                self.wildcard_manager.calculate_earned_charges(
                    raw_pts, max_raw, self.question_mistakes, was_skipped=False
                )
            )

            self.score_label.configure(text=str(self.score))
            streak = self.scoring_system.clean_streak if self.scoring_system else 0
            streak_mult = (
                self.scoring_system.calculate_streak_multiplier()
                if self.scoring_system
                else 1.0
            )

            self.stored_modal_data = {
                "correct_word": title,
                "time_taken": self.question_timer,
                "points_awarded": pts,
                "total_score": self.score,
                "question": self.current_question,
                "answer": self.current_answer,
                "was_skipped": False,
                "multiplier": mult,
                "streak": streak,
                "streak_multiplier": streak_mult,
                "charges_earned": charges_earned,
                "charges_max_reached": charges_max_reached,
            }
            self.parent.after(
                600, lambda: self.show_summary_modal_for_state(self.stored_modal_data)
            )
        else:
            self.question_mistakes += 1
            self.show_feedback(correct=False)
            if self.sfx:
                self.sfx.play("incorrect", stop_previous=True)

    def show_summary_modal_for_state(self, state, review_mode=False):
        has_prev = (
            self.viewing_history_index > 0
            if self.viewing_history_index >= 0
            else len(self.question_history) > 0
        )

        if review_mode:
            on_next = self.on_review_modal_next
            on_close = self.on_review_modal_close
            on_prev = self.on_review_modal_previous
        else:
            on_next = self.on_modal_next
            on_close = self.on_modal_close
            on_prev = self.on_modal_previous

        self.summary_modal = QuestionSummaryModal(
            self.parent,
            state["correct_word"],
            state["time_taken"],
            state["points_awarded"],
            state["total_score"],
            on_next,
            on_close,
            on_prev,
            has_prev,
            state.get("multiplier", 1),
            self.on_modal_main_menu,
            state.get("streak", 0),
            state.get("streak_multiplier", 1.0),
            state.get("charges_earned", 0),
            state.get("charges_max_reached", False),
            self.get_current_scale(),
        )
        self.summary_modal.show()

    def on_modal_main_menu(self):
        self.return_to_menu()

    def show_completion_modal_again(self):
        if self.completion_modal is None:
            stats = (
                self.scoring_system.get_session_stats() if self.scoring_system else None
            )
            self.completion_modal = GameCompletionModal(
                self.parent,
                self.score,
                len(self.questions),
                stats,
                self.on_completion_previous,
                bool(self.question_history),
                self.return_to_menu,
                self.get_current_scale(),
            )
        self.completion_modal.show()

    def on_completion_previous(self):
        if not self.question_history:
            self.show_completion_modal_again()
            return
        self.viewing_history_index = len(self.question_history) - 1
        self.load_history_state(self.viewing_history_index)

    def on_review_modal_next(self):
        if 0 <= self.viewing_history_index < len(self.question_history) - 1:
            self.viewing_history_index += 1
            self.load_history_state(self.viewing_history_index)
        else:
            self.viewing_history_index = -1
            self.show_completion_modal_again()

    def on_review_modal_close(self):
        self.on_modal_close()

    def on_review_modal_previous(self):
        if self.viewing_history_index > 0:
            self.viewing_history_index -= 1
            self.load_history_state(self.viewing_history_index)

    def on_modal_next(self):
        if self.viewing_history_index >= 0:
            if self.viewing_history_index < len(self.question_history) - 1:
                self.viewing_history_index += 1
                self.load_history_state(self.viewing_history_index)
            else:
                self.return_to_current_question()
        else:
            if self.stored_modal_data:
                self.question_history.append(self.stored_modal_data)
                # Limitar tamaño del historial para evitar crecimiento ilimitado de memoria
                if len(self.question_history) > self.MAX_QUESTION_HISTORY:
                    self.question_history = self.question_history[
                        -self.MAX_QUESTION_HISTORY :
                    ]
            self.awaiting_modal_decision = False
            self.stored_modal_data = None
            self.set_buttons_enabled(True)
            self.load_random_question()
            if not self.game_completed and self.current_question:
                self.start_timer()

    def on_modal_close(self):
        self.awaiting_modal_decision = True
        self.set_buttons_enabled(False)

    def on_modal_previous(self):
        if self.viewing_history_index >= 0:
            if self.viewing_history_index > 0:
                self.viewing_history_index -= 1
                self.load_history_state(self.viewing_history_index)
        elif self.question_history:
            self.viewing_history_index = len(self.question_history) - 1
            self.load_history_state(self.viewing_history_index)

    def load_history_state(self, idx):
        if idx < 0 or idx >= len(self.question_history):
            return

        state = self.question_history[idx]
        self.viewing_history_index = idx
        self.current_question = state["question"]
        self.current_answer = state["answer"]

        self.set_definition_text(
            self.current_question.get("definition", "No definition")
        )
        self.create_answer_boxes(
            len(self.current_question.get("title", "").replace(" ", ""))
        )
        self.update_answer_boxes()

        m, s = divmod(state["time_taken"], 60)
        self.timer_label.configure(text=f"{m:02d}:{s:02d}")
        self.score_label.configure(text=str(state["total_score"]))

        self.load_question_image()
        self.show_feedback(
            skipped=state.get("was_skipped", False),
            correct=not state.get("was_skipped", False),
        )
        self.set_buttons_enabled(False)
        self.awaiting_modal_decision = True

    def return_to_current_question(self):
        self.viewing_history_index = -1
        if not self.stored_modal_data:
            self.awaiting_modal_decision = False
            self.set_buttons_enabled(True)
            return

        state = self.stored_modal_data
        self.current_question = state["question"]
        self.current_answer = state["answer"]

        self.set_definition_text(
            self.current_question.get("definition", "No definition")
        )
        self.create_answer_boxes(
            len(self.current_question.get("title", "").replace(" ", ""))
        )
        self.update_answer_boxes()

        m, s = divmod(state["time_taken"], 60)
        self.timer_label.configure(text=f"{m:02d}:{s:02d}")
        self.score_label.configure(text=str(state["total_score"]))

        self.load_question_image()
        self.show_feedback(
            skipped=state.get("was_skipped", False),
            correct=not state.get("was_skipped", False),
        )
        self.set_buttons_enabled(False)
        self.awaiting_modal_decision = True

    def set_buttons_enabled(self, enabled):
        st = "normal" if enabled else "disabled"
        for btn in self.key_button_map.values():
            self.safe_configure(btn, state=st)
        for btn in [
            self.delete_button,
            self.skip_button,
            self.audio_toggle_btn,
            self.wildcard_x2_btn,
            self.wildcard_hint_btn,
            self.wildcard_freeze_btn,
        ]:
            if btn:
                self.safe_configure(btn, state=st)

    def show_feedback(self, correct=True, skipped=False):
        if self.feedback_animation_job:
            try:
                self.parent.after_cancel(self.feedback_animation_job)
            except tk.TclError:
                pass
            self.feedback_animation_job = None

        if skipped:
            txt, clr = "⏭ Skipped", self.COLORS.get("warning_yellow", "#FFC553")
        elif correct:
            txt, clr = "✓ Correct!", self.COLORS["feedback_correct"]
        else:
            txt, clr = "✗ Incorrect - Try Again", self.COLORS["feedback_incorrect"]

        self.feedback_label.configure(text=txt, text_color=clr)
        self.animate_feedback(0, clr)

    def animate_feedback(self, step, target):
        if step > 5:
            self.feedback_animation_job = None
            return
        if step == 0:
            self.feedback_label.configure(text_color="#F5F7FA")
        else:
            self.feedback_label.configure(
                text_color=self.interp_color("#F5F7FA", target, step / 5)
            )
        if step < 5:
            self.feedback_animation_job = self.parent.after(
                40, lambda: self.animate_feedback(step + 1, target)
            )
        else:
            self.feedback_animation_job = None

    def interp_color(self, c1, c2, f):
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        r = int(r1 + (r2 - r1) * f)
        g = int(g1 + (g2 - g1) * f)
        b = int(b1 + (b2 - b1) * f)
        return f"#{r:02x}{g:02x}{b:02x}"

    def hide_feedback(self):
        if self.feedback_animation_job:
            try:
                self.parent.after_cancel(self.feedback_animation_job)
            except tk.TclError:
                pass
            self.feedback_animation_job = None
        self.feedback_label.configure(text="")

    def start_timer(self):
        self.timer_running = True
        # Incrementar generación para invalidar callbacks de temporizador pendientes
        self.timer_generation += 1
        current_gen = self.timer_generation
        if self.timer_job:
            try:
                self.parent.after_cancel(self.timer_job)
            except tk.TclError:
                pass
            self.timer_job = None
        self.timer_job = self.parent.after(
            1000, lambda gen=current_gen: self.update_timer(gen)
        )

    def stop_timer(self):
        self.timer_running = False
        # Incrementar generación para invalidar callbacks de temporizador pendientes
        self.timer_generation += 1
        if self.timer_job:
            try:
                self.parent.after_cancel(self.timer_job)
            except tk.TclError:
                pass
            self.timer_job = None

    def update_timer(self, generation=None):
        # Verificar si este callback pertenece a la generación actual del temporizador
        if generation is not None and generation != self.timer_generation:
            return  # Callback obsoleto, ignorar
        if not self.timer_running:
            self.timer_job = None
            return
        self.question_timer += 1
        m, s = divmod(self.question_timer, 60)
        self.timer_label.configure(text=f"{m:02d}:{s:02d}")
        if self.timer_running:  # Verificar antes de programar
            current_gen = self.timer_generation
            self.timer_job = self.parent.after(
                1000, lambda gen=current_gen: self.update_timer(gen)
            )
        else:
            self.timer_job = None
