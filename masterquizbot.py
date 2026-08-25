import tkinter as tk
import random
from tkinter import messagebox, ttk

# -------------------------------------------------------------------
# QUESTION BANK (Organized by Category and Difficulty)
# -------------------------------------------------------------------
QUIZ_BANK = {
    "Maths": {
        "Easy": [
        {"question": "What is 2 + 2?", "answer": "4"},
        {"question": "What is 10 - 3?", "answer": "7"},
        {"question": "What is 5 * 6?", "answer": "30"},
        {"question": "What is 20 / 5?", "answer": "4"},
        {"question": "What is 11 + 9?", "answer": "20"},
        {"question": "What is 6 + 7?", "answer": "13"},
        {"question": "What is 8 * 4?", "answer": "32"},
        {"question": "What is 50 - 18?", "answer": "32"},
        ],
        "Medium": [
        {"question": "What is 12 / 4?", "answer": "3"},
        {"question": "What is 7 + 8?", "answer": "15"},
        {"question": "What is 9 * 9?", "answer": "81"},
        {"question": "What is 25% of 80?", "answer": "20"},
        {"question": "What is 3 squared plus 4 squared?", "answer": "25"},
        {"question": "What is 144 / 12?", "answer": "12"},
        {"question": "What is 2.5 * 4?", "answer": "10"},
        {"question": "What is the average of 6 and 14?", "answer": "10"},
        ],
        "Hard": [
        {"question": "What is the square root of 144?", "answer": "12"},
        {"question": "What is 15% of 200?", "answer": "30"},
        {"question": "If x + 7 = 19, what is x?", "answer": "12"},
        {"question": "What is the value of 2 cubed + 3 cubed?", "answer": "35"},
        {"question": "What is the greatest common factor of 48 and 60?", "answer": "12"},
        {"question": "Solve: 3x = 27.", "answer": "9"},
        {"question": "What is the next prime number after 29?", "answer": "31"},
        {"question": "What is 5 factorial?", "answer": "120"},
        ],
    },
    "Geography": {
        "Easy": [
        {"question": "What is the capital of Japan?", "answer": "Tokyo"},
        {"question": "What is the capital of France?", "answer": "Paris"},
        {"question": "Which continent is India in?", "answer": "Asia"},
        {"question": "What is the capital of Canada?", "answer": "Ottawa"},
        {"question": "Which planet is known as the Red Planet?", "answer": "Mars"},
        {"question": "What is the capital of India?", "answer": "New Delhi"},
        {"question": "How many continents are there?", "answer": "7"},
        {"question": "Which country is shaped like a boot?", "answer": "Italy"},
        ],
        "Medium": [
        {"question": "What is the largest ocean on Earth?", "answer": "Pacific"},
        {"question": "What is the capital of Germany?", "answer": "Berlin"},
        {"question": "Which country has the city of Sydney?", "answer": "Australia"},
        {"question": "Which desert is the largest hot desert?", "answer": "Sahara"},
        {"question": "What is the longest river in South America?", "answer": "Amazon"},
        {"question": "Which mountain range contains Mount Everest?", "answer": "Himalayas"},
        {"question": "What is the capital of Brazil?", "answer": "Brasilia"},
        {"question": "Which country is also called the Land of the Rising Sun?", "answer": "Japan"},
        ],
        "Hard": [
        {"question": "What is the smallest country in the world?", "answer": "Vatican City"},
        {"question": "Which strait separates Europe and Africa?", "answer": "Strait of Gibraltar"},
        {"question": "What is the capital of Mongolia?", "answer": "Ulaanbaatar"},
        {"question": "Which country has the most time zones?", "answer": "France"},
        {"question": "What is the deepest ocean trench?", "answer": "Mariana Trench"},
        {"question": "Which lake is the deepest in the world?", "answer": "Lake Baikal"},
        {"question": "What is the only continent with no permanent residents?", "answer": "Antarctica"},
        {"question": "Which two countries share the longest international border?", "answer": "Canada and United States"},
        ],
    },
    "Python": {
        "Easy": [
        {"question": "Which keyword defines a function in Python?", "answer": "def"},
        {"question": "What data type stores True or False?", "answer": "boolean"},
        {"question": "Which symbol starts a comment in Python?", "answer": "#"},
        {"question": "Which brackets create a list in Python?", "answer": "[]"},
        {"question": "What function displays text in Python?", "answer": "print"},
        {"question": "Which extension is commonly used for Python files?", "answer": ".py"},
        {"question": "Which keyword creates a loop over items?", "answer": "for"},
        {"question": "What value represents no value in Python?", "answer": "None"},
        ],
        "Medium": [
        {"question": "Which method adds an item to the end of a list?", "answer": "append"},
        {"question": "What does len([10, 20, 30]) return?", "answer": "3"},
        {"question": "Which keyword is used to handle an exception?", "answer": "except"},
        {"question": "Which data type stores key-value pairs?", "answer": "dictionary"},
        {"question": "What does the // operator perform?", "answer": "floor division"},
        {"question": "Which method removes and returns the last list item?", "answer": "pop"},
        {"question": "What does str(25) return?", "answer": "25"},
        {"question": "Which keyword imports a module?", "answer": "import"},
        ],
        "Hard": [
        {"question": "What is the output of print(2 ** 3)?", "answer": "8"},
        {"question": "Which built-in function creates a sequence of numbers?", "answer": "range"},
        {"question": "What does the == operator compare?", "answer": "value"},
        {"question": "Which keyword creates an anonymous function?", "answer": "lambda"},
        {"question": "What does a Python decorator modify?", "answer": "function"},
        {"question": "What is the purpose of __init__ in a class?", "answer": "initialize"},
        {"question": "Which collection type cannot be changed after creation?", "answer": "tuple"},
        {"question": "What exception occurs when dividing by zero?", "answer": "ZeroDivisionError"},
        ],
    }
}

FILE_NAME = "scores.txt"

# -------------------------------------------------------------------
# GUI APPLICATION
# -------------------------------------------------------------------
class QuizMasterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Master Bot")
        self.root.geometry("500x540")
        self.root.resizable(False, False)

        # Game State Variables
        self.player_name = ""
        self.category = ""
        self.difficulty = ""
        self.questions = []
        self.current_index = 0
        self.score = 0
        self.last_question_set = None

        # Frame Container
        self.main_frame = tk.Frame(self.root, padx=20, pady=20)
        self.main_frame.pack(fill="both", expand=True)

        self.show_welcome_screen()

    def clear_frame(self):
        """Removes all widgets from current screen."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # --- SCREEN 1: SETUP (Name, Category, Difficulty) ---
    def show_welcome_screen(self):
        self.clear_frame()

        tk.Label(self.main_frame, text="QUIZ MASTER", font=("Helvetica", 22, "bold"), fg="#17324D").pack(pady=(8, 2))
        tk.Label(self.main_frame, text="Choose your challenge and test your knowledge", font=("Helvetica", 10), fg="#607080").pack(pady=(0, 18))

        # 1. Player Name Input
        tk.Label(self.main_frame, text="Enter Your Name:", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(10, 2))
        self.name_entry = tk.Entry(self.main_frame, font=("Helvetica", 11))
        self.name_entry.pack(fill="x", pady=5)
        self.name_entry.insert(0, "Player")

        # 2. Category Selection
        tk.Label(self.main_frame, text="Select Category:", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(10, 2))
        self.category_var = tk.StringVar(value=list(QUIZ_BANK.keys())[0])
        category_dropdown = ttk.Combobox(
            self.main_frame, 
            textvariable=self.category_var, 
            values=list(QUIZ_BANK.keys()), 
            state="readonly",
            font=("Helvetica", 10)
        )
        category_dropdown.pack(fill="x", pady=5)

        # 3. Difficulty Level Selection
        tk.Label(self.main_frame, text="Select Difficulty:", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(14, 5))
        self.difficulty_var = tk.StringVar(value="Easy")
        diff_frame = tk.Frame(self.main_frame)
        diff_frame.pack(fill="x", pady=5)
        self.difficulty_buttons = []
        for level, color, hover_color, selected_color in (
            ("Easy", "#2E8B57", "#246B45", "#185C38"),
            ("Medium", "#D17B0F", "#A85F0B", "#874B08"),
            ("Hard", "#B44343", "#8E3030", "#6F2424"),
        ):
            difficulty_button = tk.Radiobutton(
                diff_frame, text=level, variable=self.difficulty_var, value=level,
                bg=color, fg="white", activebackground=hover_color, activeforeground="white",
                font=("Helvetica", 10, "bold"), indicatoron=False, width=9, pady=9,
                selectcolor=selected_color, relief="raised", overrelief="sunken", bd=0,
                highlightthickness=0, cursor="hand2"
            )
            difficulty_button.pack(side="left", expand=True, padx=4)
            self.difficulty_buttons.append((difficulty_button, color, selected_color))

        def refresh_difficulty_buttons(*args):
            selected_level = self.difficulty_var.get()
            for button, color, selected_color in self.difficulty_buttons:
                is_selected = button.cget("value") == selected_level
                button.configure(
                    bg=selected_color if is_selected else color,
                    relief="sunken" if is_selected else "raised"
                )

        self.difficulty_var.trace_add("write", refresh_difficulty_buttons)
        refresh_difficulty_buttons()

        # Action Buttons
        tk.Button(
            self.main_frame, text="START QUIZ", font=("Helvetica", 11, "bold"),
            bg="#E67E22", fg="#17324D", activebackground="#B95D0B", command=self.start_quiz
        ).pack(fill="x", pady=(20, 5))

        tk.Button(
            self.main_frame, text="View Leaderboard", font=("Helvetica", 10), 
            command=self.show_leaderboard
        ).pack(fill="x", pady=5)

    # --- SCREEN 2: ACTIVE QUIZ ---
    def start_quiz(self):
        self.player_name = self.name_entry.get().strip() or "Player"
        self.category = self.category_var.get()
        self.difficulty = self.difficulty_var.get()
        
        question_pool = QUIZ_BANK[self.category][self.difficulty]
        question_set = random.sample(question_pool, 5)
        question_signature = tuple(sorted(item["question"] for item in question_set))
        while question_signature == self.last_question_set:
            question_set = random.sample(question_pool, 5)
            question_signature = tuple(sorted(item["question"] for item in question_set))
        self.questions = question_set
        self.last_question_set = question_signature

        self.current_index = 0
        self.score = 0
        self.show_question_screen()

    def show_question_screen(self):
        self.clear_frame()

        q_data = self.questions[self.current_index]

        # Header Info
        header_text = f"{self.category.upper()}  /  {self.difficulty.upper()}"
        tk.Label(self.main_frame, text=header_text, font=("Helvetica", 9, "bold"), fg="#607080").pack(anchor="w")
        tk.Label(self.main_frame, text=f"Question {self.current_index + 1} of {len(self.questions)}   •   Score: {self.score}", font=("Helvetica", 10), fg="#17324D").pack(anchor="w", pady=(5, 3))
        progress = ttk.Progressbar(self.main_frame, length=420, mode="determinate", maximum=len(self.questions), value=self.current_index + 1)
        progress.pack(fill="x", pady=(0, 18))
        
        # Question Display
        tk.Label(
            self.main_frame, text=q_data["question"], 
            font=("Helvetica", 15, "bold"), wraplength=420, justify="left", fg="#17324D"
        ).pack(pady=20, anchor="w")

        # Answer Input
        tk.Label(self.main_frame, text="Your Answer:", font=("Helvetica", 10)).pack(anchor="w")
        self.answer_entry = tk.Entry(self.main_frame, font=("Helvetica", 11))
        self.answer_entry.pack(fill="x", pady=5)
        self.answer_entry.focus()
        self.answer_entry.bind("<Return>", lambda event: self.submit_answer())

        # Submit Button
        tk.Button(
            self.main_frame, text="SUBMIT ANSWER", font=("Helvetica", 11, "bold"),
            bg="#2E8B57", fg="#17324D", activebackground="#246B45", command=self.submit_answer
        ).pack(fill="x", pady=15)

    def submit_answer(self):
        user_ans = self.answer_entry.get().strip().lower()
        correct_ans = self.questions[self.current_index]["answer"].lower()

        if user_ans == correct_ans:
            self.score += 1
            messagebox.showinfo("Result", "Correct!")
        else:
            messagebox.showerror("Result", f"Wrong!\nCorrect Answer: {self.questions[self.current_index]['answer']}")

        self.current_index += 1

        if self.current_index < len(self.questions):
            self.show_question_screen()
        else:
            self.finish_quiz()

    # --- SCREEN 3: END SCREEN & SAVE RESULTS ---
    def finish_quiz(self):
        self.clear_frame()

        # Save result directly to file (Day 17/25)
        with open(FILE_NAME, "a") as file:
            file.write(f"{self.player_name} scored {self.score}/{len(self.questions)} in [{self.category} - {self.difficulty}]\n")

        tk.Label(self.main_frame, text="Quiz Finished!", font=("Helvetica", 16, "bold")).pack(pady=10)
        tk.Label(
            self.main_frame, 
            text=f"Great job, {self.player_name}!\nYour Score: {self.score} / {len(self.questions)}", 
            font=("Helvetica", 12)
        ).pack(pady=10)

        # Performance Message
        if self.score == len(self.questions):
            msg = "Perfect Score! Amazing work!"
        elif self.score >= len(self.questions) / 2:
            msg = "Good job! Keep going!"
        else:
            msg = "Keep practicing!"
            
        tk.Label(self.main_frame, text=msg, font=("Helvetica", 11, "italic"), fg="#444").pack(pady=5)
        tk.Label(self.main_frame, text="Your result has been saved to scores.txt", font=("Helvetica", 9), fg="green").pack(pady=5)

        tk.Button(
            self.main_frame, text="Play Again", font=("Helvetica", 11, "bold"), 
            bg="#4CAF50", fg="#17324D", command=self.show_welcome_screen
        ).pack(fill="x", pady=(15, 5))

    # --- SCREEN 4: LEADERBOARD DISPLAY ---
    def show_leaderboard(self):
        self.clear_frame()

        tk.Label(self.main_frame, text="Leaderboard", font=("Helvetica", 16, "bold")).pack(pady=10)

        # Text Widget to show saved scores
        score_box = tk.Text(self.main_frame, height=12, width=50, font=("Helvetica", 9))
        score_box.pack(pady=5)

        try:
            with open(FILE_NAME, "r") as file:
                scores = file.readlines()
                if not scores:
                    score_box.insert(tk.END, "No saved scores yet.")
                else:
                    for line in scores:
                        score_box.insert(tk.END, "- " + line)
        except FileNotFoundError:
            score_box.insert(tk.END, "No saved scores yet.")

        score_box.config(state="disabled")

        tk.Button(
            self.main_frame, text="Back to Menu", font=("Helvetica", 10), 
            command=self.show_welcome_screen
        ).pack(fill="x", pady=10)

# -------------------------------------------------------------------
# MAIN RUNNER
# -------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = QuizMasterGUI(root)
    root.mainloop()