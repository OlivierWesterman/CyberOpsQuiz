import os
import json
import random
import shutil
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TypedDict
from PIL import Image, ImageTk


CACHE_DIR = ".cache"
CACHE_CORRECT = os.path.join(CACHE_DIR, "correct")


class Question(TypedDict):
    question: str
    options: list[str]
    correct: int | list[int]
    image: str | None


def resource_path(relative_path: str) -> str:
    # Get the directory where the script is located
    # script_dir = os.path.dirname(os.path.abspath(__file__))
    # # Construct absolute path, removing any duplicate path segments
    # full_path = os.path.normpath(os.path.join(script_dir, "Images", relative_path))
    return os.path.join(*relative_path.split("/"))


def save_questions_to_files(questions: list[Question]):
    # Ensure the questions directory exists
    os.makedirs(os.path.join("questions"), exist_ok=True)
    os.makedirs(os.path.join("questions", "images"), exist_ok=True)

    for i, question in enumerate(questions):
        q_num = i + 1
        file_path = os.path.join("questions", f"{q_num}.json")

        # If the question has an image, copy it to the images directory
        if question["image"]:
            image_path = os.path.abspath(resource_path(question["image"]))
            shutil.copy(
                image_path,
                os.path.abspath(
                    os.path.join(
                        "questions",
                        "images",
                        f"image-{q_num}.{os.path.basename(image_path).split(".")[-1]}",
                    )
                ),
            )
            question["image"] = (
                f"images/image-{q_num}.{os.path.basename(image_path).split('.')[-1]}"
            )

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(question, file, indent=4)


class QuizApp(tk.Frame):
    selected_questions: list[str]
    current_question: int
    score: int
    current_correct_answers: list[int]
    current_image: ImageTk.PhotoImage | None
    answer_buttons: list[ttk.Button]
    answer_vars: list[tk.IntVar]

    def __init__(self, root: tk.Tk):
        super().__init__(root)
        self.root = root
        self.root.title("CCNA Quiz")
        self.root.geometry("1000x800")

        cached_correct = self.get_cached_correct()

        self.questions: list[str] = [
            os.path.join("questions", file)
            for file in os.listdir("questions")
            if file not in cached_correct
        ]

        self.setup_ui()

    def setup_ui(self):
        ttk.Label(self.root, text="Aantal vragen:").pack(pady=5)
        self.question_count = ttk.Spinbox(self.root, from_=1, to=len(self.questions))
        self.question_count.pack()
        ttk.Button(
            self.root,
            text="Alle vragen",
            command=lambda: self.question_count.set(len(self.questions)),
        ).pack(pady=5)

        ttk.Button(self.root, text="Start Quiz", command=self.start_quiz).pack(pady=5)

        self.quiz_frame = ttk.Frame(self.root)
        self.quiz_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        self.counter_label = ttk.Label(self.quiz_frame, text="")
        self.counter_label.pack(pady=5)

        self.question_label = ttk.Label(self.quiz_frame, text="", wraplength=700)
        self.question_label.pack(pady=20)

        self.answer_vars = []
        self.answer_buttons = []
        self.answers_frame = ttk.Frame(self.quiz_frame)
        self.answers_frame.pack(pady=10)

        self.submit_btn = ttk.Button(
            self.quiz_frame, text="Controleer Antwoord", command=self.check_answer
        )
        self.submit_btn.pack(pady=20)

        self.next_btn = ttk.Button(
            self.quiz_frame, text="Volgende Vraag", command=self.next_question
        )
        self.next_btn.pack(pady=10)
        self.next_btn.pack_forget()

        self.image_label = ttk.Label(self.quiz_frame)
        self.image_label.pack(pady=10)

        self.quiz_frame.pack_forget()

    def start_quiz(self):
        num_questions = int(self.question_count.get())
        if num_questions > len(self.questions):
            messagebox.showerror(  # type: ignore
                "Error", f"Maximum aantal vragen is {len(self.questions)}"
            )
            return

        self.selected_questions = random.sample(self.questions, num_questions)
        self.current_question = 0
        self.score = 0
        self.quiz_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        self.show_question()

    def show_question(self):
        if self.current_question >= len(self.selected_questions):
            self.show_results()
            return

        # Pick question from selected questions
        question = self.get_current_question()
        self.question_label.config(text=question["question"])

        self.counter_label.config(
            text=f"Vraag {self.current_question + 1}/{len(self.selected_questions)}"
        )

        if image_path := question.get("image"):
            try:
                # Extract just the filename from the path
                image_filename = os.path.basename(image_path)
                # Get full path using resource_path
                full_path = os.path.join("questions", "images", image_filename)

                image = Image.open(full_path)
                image = image.resize((400, 300), Image.Resampling.LANCZOS)  # type: ignore
                photo = ImageTk.PhotoImage(image)
                self.image_label.config(image=photo)  # type: ignore
                self.image_label.image = photo  # type: ignore
                self.image_label.pack(pady=10)
            except (FileNotFoundError, IOError) as e:
                print(f"Error loading image: {e}")
                self.image_label.pack_forget()
        else:
            self.image_label.pack_forget()

        correct_answers = (
            question["correct"]
            if isinstance(question["correct"], list)
            else [question["correct"]]
        )
        option_pairs = [
            (opt, i in correct_answers) for i, opt in enumerate(question["options"])
        ]
        random.shuffle(option_pairs)

        options, correct_statuses = zip(*option_pairs)
        self.current_correct_answers = [
            i for i, is_correct in enumerate(correct_statuses) if is_correct
        ]

        for btn in self.answer_buttons:
            btn.destroy()
        self.answer_vars.clear()
        self.answer_buttons.clear()

        for option in options:
            var = tk.IntVar()
            btn = tk.Checkbutton(
                self.answers_frame, text=option, variable=var, padx=20, pady=5
            )
            btn.pack(anchor="w")
            self.answer_vars.append(var)
            self.answer_buttons.append(btn)  # type: ignore

        self.submit_btn.config(state="normal")
        self.next_btn.pack_forget()

    def next_question(self):
        self.current_question += 1
        self.show_question()

    def show_results(self):
        for widget in self.quiz_frame.winfo_children():
            widget.destroy()

        score_percentage = (self.score / len(self.selected_questions)) * 100
        result_text = f"Quiz voltooid!\nScore: {self.score}/{len(self.selected_questions)}\nPercentage: {score_percentage:.2f}%"
        ttk.Label(self.quiz_frame, text=result_text).pack(pady=20)
        ttk.Button(self.quiz_frame, text="Opnieuw", command=self.reset_quiz).pack()

    def reset_quiz(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_ui()

    def get_question(self, question_num: int) -> Question:
        with open(self.selected_questions[question_num], "r", encoding="utf-8") as file:
            return json.load(file)

    def get_current_question(self) -> Question:
        return self.get_question(self.current_question)

    def get_cached_correct(self) -> list[str]:
        if not os.path.exists(CACHE_CORRECT):
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(CACHE_CORRECT, "w", encoding="utf-8") as file:
                pass
            return []

        with open(CACHE_CORRECT, "r", encoding="utf-8") as file:
            return [f.strip() for f in file.readlines()]

    def check_answer(self):
        selected_answers = [
            i for i, var in enumerate(self.answer_vars) if var.get() == 1
        ]

        if set(selected_answers) == set(self.current_correct_answers):
            self.score += 1
            self.highlight_correct_selections(self.current_correct_answers)

            # Cache correct answer
            os.makedirs(".cache", exist_ok=True)
            with open(CACHE_CORRECT, "a", encoding="utf-8") as file:
                file.write(f"{os.path.basename(self.selected_questions[self.current_question])}\n")
        else:
            self.highlight_wrong_selections(
                selected_answers, self.current_correct_answers
            )

        self.submit_btn.config(state="disabled")
        self.next_btn.pack(pady=10)

    def highlight_correct_selections(self, correct_indices: list[int]):
        for i, btn in enumerate(self.answer_buttons):
            if i in correct_indices:
                btn.config(bg="green")  # type: ignore
            else:
                btn.config(bg="grey")  # type: ignore

    def highlight_wrong_selections(
        self, selected_indices: list[int], correct_indices: list[int]
    ):
        for i, btn in enumerate(self.answer_buttons):
            if i in selected_indices and i not in correct_indices:
                btn.config(bg="red")  # type: ignore
            elif i in correct_indices:
                btn.config(bg="green")  # type: ignore
            else:
                btn.config(bg="grey")  # type: ignore


if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()
