import os
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

    def on_wildcard_x2(self):
        if (
            not self.current_question
            or self.awaiting_modal_decision
            or self.viewing_history_index >= 0
        ):
            return
        stacks = self.wildcard_manager.activate_double_points()
        if stacks > 0:
            self.wildcard_x2_btn.configure(
                text=f"X{self.wildcard_manager.get_points_multiplier()}"
            )
            self.update_wildcard_buttons_state()

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

    def load_random_question(self):
        self.tts.stop()
        self.hide_feedback()
        self.processing_correct_answer = False
        self.wildcard_manager.reset_for_new_question()
        self.update_wildcard_buttons_state()
        self.reset_timer_visuals()

        if not self.questions:
            self.definition_label.configure(text="No questions available!")
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
        self.definition_label.configure(text=definition)
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
            return
        try:
            if not os.path.isabs(image_path):
                image_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), image_path
                )
            if os.path.exists(image_path):
                pil_img = Image.open(image_path).convert("RGBA")
                max_sz = self.get_scaled_image_size()
                w, h = pil_img.size
                sc = min(max_sz / w, max_sz / h)
                self.current_image = ctk.CTkImage(
                    light_image=pil_img,
                    dark_image=pil_img,
                    size=(int(w * sc), int(h * sc)),
                )
                self.image_label.configure(image=self.current_image, text="")
            else:
                self.image_label.configure(image=None, text="Image not found")
        except (FileNotFoundError, OSError, ValueError) as e:
            print(f"Error loading image: {e}")
            self.image_label.configure(image=None, text="Error loading image")

    def on_key_press(self, key):
        if not self.current_question or self.awaiting_modal_decision:
            return
        title = self.current_question.get("title", "").replace(" ", "")
        max_len = len(title)
        revealed = self.wildcard_manager.get_revealed_positions()

        if key == "⌫":
            if self.current_answer:
                ans = list(self.current_answer)
                for i in range(len(ans) - 1, -1, -1):
                    if i in revealed or not ans[i] or ans[i] == " ":
                        continue
                    ans[i] = ""
                    break
                while (
                    ans
                    and (len(ans) - 1) not in revealed
                    and (not ans[-1] or ans[-1] == " ")
                ):
                    ans.pop()
                self.current_answer = "".join(ans)
        else:
            ans = list(self.current_answer)
            while len(ans) < max_len:
                ans.append("")
            for i in range(max_len):
                if i not in revealed and (not ans[i] or ans[i] == " "):
                    ans[i] = key
                    break
            while ans and (not ans[-1] or ans[-1] == " "):
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
            lambda: self._safe_configure(box, fg_color=self.COLORS["success_green"]),
        )

    def _safe_configure(self, widget, **kw):
        try:
            widget.configure(**kw)
        except tk.TclError:
            pass

    def toggle_audio(self):
        self.audio_enabled = not self.audio_enabled
        self.update_audio_button_icon()
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
            self.skip_modal = SkipConfirmationModal(self.parent, self.do_skip)
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

        # Calculate charges for skip (for anti-frustration tracking)
        charges_earned = self.wildcard_manager.calculate_earned_charges(
            0, 1, 0, was_skipped=True
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
            "current_image": self.current_image,
            "was_skipped": True,
            "multiplier": 1,
            "streak": streak,
            "streak_multiplier": streak_mult,
            "charges_earned": charges_earned,
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
        self.definition_label.configure(text="Game Complete!")
        stats = self.scoring_system.get_session_stats() if self.scoring_system else None
        self.completion_modal = GameCompletionModal(
            self.parent,
            self.score,
            len(self.questions),
            stats,
            self.on_completion_previous,
            bool(self.question_history),
            self.return_to_menu,
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
        if self.current_answer.upper() == title.replace(" ", "").upper():
            self.processing_correct_answer = True
            self.stop_timer()
            self.tts.stop()
            self.show_feedback(correct=True)
            pts = 0
            raw_pts = 0
            max_raw = 0
            mult = self.wildcard_manager.get_points_multiplier()
            if self.scoring_system:
                # Calculate raw points for charge earning
                effective_time = self.scoring_system.get_effective_time(
                    self.question_timer
                )
                raw_pts = self.scoring_system.calculate_raw_points(effective_time)
                max_raw = self.scoring_system.max_raw_per_question

                res = self.scoring_system.process_correct_answer(
                    time_seconds=self.question_timer, mistakes=self.question_mistakes
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

            # Calculate earned charges
            charges_earned = self.wildcard_manager.calculate_earned_charges(
                raw_pts, max_raw, self.question_mistakes, was_skipped=False
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
                "current_image": self.current_image,
                "was_skipped": False,
                "multiplier": mult,
                "streak": streak,
                "streak_multiplier": streak_mult,
                "charges_earned": charges_earned,
            }
            self.parent.after(
                600, lambda: self.show_summary_modal_for_state(self.stored_modal_data)
            )
        else:
            self.question_mistakes += 1
            self.show_feedback(correct=False)

    def show_summary_modal_for_state(self, state, review_mode=False):
        has_prev = (
            self.viewing_history_index > 0
            if self.viewing_history_index >= 0
            else len(self.question_history) > 0
        )
        if review_mode:
            on_next, on_close, on_prev = (
                self.on_review_modal_next,
                self.on_review_modal_close,
                self.on_review_modal_previous,
            )
        else:
            on_next, on_close, on_prev = (
                self.on_modal_next,
                self.on_modal_close,
                self.on_modal_previous,
            )
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
        self.definition_label.configure(
            text=self.current_question.get("definition", "No definition")
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
        self.definition_label.configure(
            text=self.current_question.get("definition", "No definition")
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
            self._safe_configure(btn, state=st)
        for btn in [
            self.delete_button,
            self.skip_button,
            self.audio_toggle_btn,
            self.wildcard_x2_btn,
            self.wildcard_hint_btn,
            self.wildcard_freeze_btn,
        ]:
            if btn:
                self._safe_configure(btn, state=st)

    def show_feedback(self, correct=True, skipped=False):
        if self.feedback_animation_job:
            self.parent.after_cancel(self.feedback_animation_job)
            self.feedback_animation_job = None
        if skipped:
            txt, clr = "⏭ Skipped", self.COLORS.get("warning_yellow", "#FFC553")
        elif correct:
            txt, clr = "✓ Correct!", self.COLORS["feedback_correct"]
        else:
            txt, clr = "✗ Incorrect - Try Again", self.COLORS["feedback_incorrect"]
        self.feedback_label.configure(text=txt, text_color=clr)
        self._animate_feedback(0, clr)

    def _animate_feedback(self, step, target):
        if step > 5:
            return
        if step == 0:
            self.feedback_label.configure(text_color="#F5F7FA")
        else:
            self.feedback_label.configure(
                text_color=self._interp_color("#F5F7FA", target, step / 5)
            )
        if step < 5:
            self.feedback_animation_job = self.parent.after(
                40, lambda: self._animate_feedback(step + 1, target)
            )

    def _interp_color(self, c1, c2, f):
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        r = int(r1 + (r2 - r1) * f)
        g = int(g1 + (g2 - g1) * f)
        b = int(b1 + (b2 - b1) * f)
        return f"#{r:02x}{g:02x}{b:02x}"

    def hide_feedback(self):
        if self.feedback_animation_job:
            self.parent.after_cancel(self.feedback_animation_job)
            self.feedback_animation_job = None
        self.feedback_label.configure(text="")

    def start_timer(self):
        self.timer_running = True
        if self.timer_job:
            try:
                self.parent.after_cancel(self.timer_job)
            except tk.TclError:
                pass
            self.timer_job = None
        self.timer_job = self.parent.after(1000, self.update_timer)

    def stop_timer(self):
        self.timer_running = False
        if self.timer_job:
            self.parent.after_cancel(self.timer_job)
            self.timer_job = None

    def update_timer(self):
        if not self.timer_running:
            return
        self.question_timer += 1
        m, s = divmod(self.question_timer, 60)
        self.timer_label.configure(text=f"{m:02d}:{s:02d}")
        self.timer_job = self.parent.after(1000, self.update_timer)
