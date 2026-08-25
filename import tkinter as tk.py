import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from zoneinfo import ZoneInfo

import json
import os
import re
import ast
import operator
import webbrowser
import subprocess
import threading

from ollama import chat


# ============================================================
# CONFIG
# ============================================================

APP_NAME = "TejaswiniGPT"

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2"
)

MEMORY_FILE = "memory.json"
KNOWLEDGE_FILE = "knowledge.json"


# ============================================================
# SAFE CALCULATOR
# ============================================================

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos
}


def safe_calculate(expression):

    expression = expression.replace("^", "**")

    if not re.fullmatch(
        r"[0-9+\-*/().%\s*]+",
        expression
    ):
        raise ValueError(
            "Invalid mathematical expression."
        )

    def evaluate(node):

        if isinstance(node, ast.Constant):

            if isinstance(
                node.value,
                (int, float)
            ):
                return node.value

            raise ValueError(
                "Invalid number."
            )

        if isinstance(node, ast.BinOp):

            left = evaluate(node.left)
            right = evaluate(node.right)

            operation = OPERATORS.get(
                type(node.op)
            )

            if operation is None:
                raise ValueError(
                    "Operator not allowed."
                )

            return operation(
                left,
                right
            )

        if isinstance(node, ast.UnaryOp):

            operation = OPERATORS.get(
                type(node.op)
            )

            if operation is None:
                raise ValueError(
                    "Operator not allowed."
                )

            return operation(
                evaluate(node.operand)
            )

        raise ValueError(
            "Invalid expression."
        )

    tree = ast.parse(
        expression,
        mode="eval"
    )

    return evaluate(tree.body)


# ============================================================
# MAIN AI AGENT
# ============================================================

class TejaswiniGPT:

    def __init__(self, root):

        self.root = root

        self.root.title(APP_NAME)

        self.root.geometry(
            "900x760"
        )

        self.root.minsize(
            700,
            600
        )

        # ====================================================
        # MEMORY
        # ====================================================

        self.memories = []

        self.load_memory()

        # ====================================================
        # KNOWLEDGE
        # ====================================================

        self.knowledge = {}

        self.load_knowledge()

        # ====================================================
        # STUDY BUDDY STATE MACHINE
        # ====================================================

        self.study_stage = "topic_input"

        self.study_topic = ""

        self.study_overview = ""

        self.study_quiz = []

        self.study_answers = []

        self.study_score = 0

        self.study_window = None

        self.study_answer_vars = []

        # ====================================================
        # MAIN UI
        # ====================================================

        main = ttk.Frame(
            root,
            padding=18
        )

        main.pack(
            fill="both",
            expand=True
        )

        # ====================================================
        # TITLE
        # ====================================================

        title = ttk.Label(
            main,
            text=APP_NAME,
            font=(
                "Helvetica",
                24,
                "bold"
            )
        )

        title.pack(
            anchor="w"
        )

        subtitle = ttk.Label(
            main,
            text=(
                "Local AI Agent • Ollama • Memory • "
                "Knowledge • Tools • Web Research • Study Buddy"
            )
        )

        subtitle.pack(
            anchor="w",
            pady=(2, 10)
        )

        # ====================================================
        # STATUS
        # ====================================================

        self.status = ttk.Label(
            main,
            text="● Agent Ready"
        )

        self.status.pack(
            anchor="w",
            pady=(0, 10)
        )

        # ====================================================
        # AGENT PIPELINE
        # ====================================================

        pipeline = ttk.Label(
            main,
            text=(
                "🎯 Goal → 🧠 Brain → ⚖️ Decision → "
                "⚡ Action → 💬 Output"
            )
        )

        pipeline.pack(
            anchor="w",
            pady=(0, 10)
        )

        # ====================================================
        # CHAT
        # ====================================================

        chat_frame = ttk.Frame(main)

        chat_frame.pack(
            fill="both",
            expand=True
        )

        self.chat_box = tk.Text(
            chat_frame,
            wrap="word",
            state="disabled",
            font=(
                "Helvetica",
                12
            ),
            padx=12,
            pady=12
        )

        scrollbar = ttk.Scrollbar(
            chat_frame,
            orient="vertical",
            command=self.chat_box.yview
        )

        self.chat_box.configure(
            yscrollcommand=scrollbar.set
        )

        self.chat_box.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        # ====================================================
        # WEB SEARCH
        # ====================================================

        options = ttk.Frame(main)

        options.pack(
            fill="x",
            pady=(10, 5)
        )

        self.live_web = tk.BooleanVar(
            value=False
        )

        ttk.Checkbutton(
            options,
            text="🌐 Live Web Research",
            variable=self.live_web
        ).pack(
            side="left"
        )

        ttk.Label(
            options,
            text="Search current information"
        ).pack(
            side="left",
            padx=10
        )

        # ====================================================
        # STUDY BUDDY BUTTON
        # ====================================================

        ttk.Button(
            options,
            text="📚 Study Buddy",
            command=self.start_study_from_button
        ).pack(
            side="right"
        )

        # ====================================================
        # INPUT
        # ====================================================

        input_frame = ttk.Frame(main)

        input_frame.pack(
            fill="x",
            pady=(5, 0)
        )

        ask_button = ttk.Button(
            input_frame,
            text="Ask me anything",
            command=self.focus_input
        )

        ask_button.pack(
            side="left",
            padx=(0, 8)
        )

        self.input_box = ttk.Entry(
            input_frame,
            font=(
                "Helvetica",
                12
            )
        )

        self.input_box.pack(
            side="left",
            fill="x",
            expand=True
        )

        search_button = ttk.Button(
            input_frame,
            text="Search",
            command=self.search_request
        )

        search_button.pack(
            side="left",
            padx=(8, 0)
        )

        self.input_box.bind(
            "<Return>",
            self.process_request
        )

        submit = ttk.Button(
            input_frame,
            text="Submit",
            command=self.process_request
        )

        submit.pack(
            side="left",
            padx=(8, 0)
        )

        self.input_box.focus()

        self.add_message(
            APP_NAME,
            (
                "Hello! 👋\n\n"
                "I am your local AI Agent powered by Ollama.\n\n"
                "I can answer questions, remember information, "
                "calculate, search the web, perform actions, "
                "and create interactive quizzes."
            )
        )

    # ========================================================
    # MEMORY
    # ========================================================

    def load_memory(self):

        if not os.path.exists(
            MEMORY_FILE
        ):
            return

        try:

            with open(
                MEMORY_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                self.memories = json.load(f)

        except Exception:

            self.memories = []

    # --------------------------------------------------------

    def save_memory(self):

        with open(
            MEMORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.memories,
                f,
                indent=4
            )

    # --------------------------------------------------------

    def remember(self, text):

        self.memories.append(text)

        self.save_memory()

    # ========================================================
    # KNOWLEDGE
    # ========================================================

    def load_knowledge(self):

        if os.path.exists(
            KNOWLEDGE_FILE
        ):

            try:

                with open(
                    KNOWLEDGE_FILE,
                    "r",
                    encoding="utf-8"
                ) as f:

                    self.knowledge = json.load(f)

                    return

            except Exception:

                pass

        self.knowledge = {

            "artificial intelligence":
                "AI is the field of building systems "
                "that perform tasks requiring intelligence.",

            "machine learning":
                "Machine learning allows systems to "
                "learn patterns from data.",

            "cybersecurity":
                "Cybersecurity protects systems, networks "
                "and data from digital threats.",

            "ai agent":
                "An AI agent has a goal, brain, memory, "
                "knowledge, tools, decision making and actions.",

            "tcp":
                "TCP is a connection-oriented transport protocol "
                "that provides reliable and ordered delivery.",

            "udp":
                "UDP is a connectionless transport protocol "
                "that prioritizes speed and low overhead."
        }

        with open(
            KNOWLEDGE_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.knowledge,
                f,
                indent=4
            )

    # --------------------------------------------------------

    def search_knowledge(self, question):

        question = question.lower()

        for topic, answer in self.knowledge.items():

            if topic in question:
                return answer

        return None

    # ========================================================
    # TIME / DATE / DAY
    # ========================================================

    def india_now(self):

        return datetime.now(
            ZoneInfo("Asia/Kolkata")
        )

    # --------------------------------------------------------

    def get_time(self):

        return self.india_now().strftime(
            "%I:%M:%S %p"
        )

    # --------------------------------------------------------

    def get_date(self):

        return self.india_now().strftime(
            "%d %B %Y"
        )

    # --------------------------------------------------------

    def get_day(self):

        return self.india_now().strftime(
            "%A"
        )

    # ========================================================
    # REAL-TIME DETECTOR
    # ========================================================

    def is_realtime(self, question):

        q = question.lower()

        local_intent = any(
            phrase in q
            for phrase in [

                "what time",
                "current time",
                "time now",
                "tell me the time",

                "today's date",
                "todays date",
                "current date",
                "what is the date",
                "what's the date",

                "what day",
                "which day"
            ]
        )

        if local_intent:
            return False

        keywords = [

            "latest",
            "current",
            "today",
            "today's",
            "right now",
            "recent",
            "news",
            "breaking",
            "live",
            "score",
            "scores",
            "match result",
            "stock",
            "stocks",
            "share price",
            "nifty",
            "sensex",
            "nasdaq",
            "market today",
            "recent update",
            "latest update"
        ]

        return any(
            word in q
            for word in keywords
        )

    # ========================================================
    # GOAL
    # ========================================================

    def identify_goal(self, question):

        if self.is_realtime(question):
            return "Find live information."

        q = question.lower()

        if (
            "study buddy" in q
            or "study " in q
            or "quiz me" in q
            or "create quiz" in q
        ):
            return "Create an interactive study session."

        if "time" in q:
            return "Get current time."

        if "date" in q:
            return "Get current date."

        if (
            "what day" in q
            or "which day" in q
        ):
            return "Get current day."

        if (
            "calculate" in q
            or "solve" in q
        ):
            return "Perform calculation."

        if "remember" in q:
            return "Store information in memory."

        if "open" in q:
            return "Perform computer action."

        return "Answer the user's question."

    # ========================================================
    # DECISION MAKING
    # ========================================================

    def decide_action(self, question):

        q = question.lower().strip()

        # ----------------------------------------------------
        # STUDY BUDDY
        # ----------------------------------------------------

        if (
            "study buddy" in q
            or q.startswith("study ")
            or q.startswith("quiz me")
            or q.startswith("create quiz")
            or q.startswith("start quiz")
        ):

            return "STUDY_BUDDY"

        # ----------------------------------------------------
        # TIME
        # ----------------------------------------------------

        if any(
            x in q
            for x in [
                "what time",
                "current time",
                "time now",
                "tell me the time"
            ]
        ):

            return "TIME"

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        if any(
            x in q
            for x in [
                "today's date",
                "todays date",
                "current date",
                "what is the date",
                "what's the date"
            ]
        ):

            return "DATE"

        # ----------------------------------------------------
        # DAY
        # ----------------------------------------------------

        if any(
            x in q
            for x in [
                "what day",
                "which day",
                "what day is today"
            ]
        ):

            return "DAY"

        # ----------------------------------------------------
        # CALCULATOR
        # ----------------------------------------------------

        if (
            q.startswith("calculate ")
            or q.startswith("solve ")
        ):

            return "CALCULATOR"

        # ----------------------------------------------------
        # MEMORY
        # ----------------------------------------------------

        if q.startswith(
            "remember "
        ):

            return "MEMORY"

        if (
            "what do you remember" in q
            or "show memory" in q
        ):

            return "SHOW_MEMORY"

        # ----------------------------------------------------
        # ACTIONS
        # ----------------------------------------------------

        if "open youtube" in q:
            return "YOUTUBE"

        if "open google" in q:
            return "GOOGLE"

        if "open github" in q:
            return "GITHUB"

        if "open calculator" in q:
            return "MAC_CALCULATOR"

        if "open terminal" in q:
            return "TERMINAL"

        # ----------------------------------------------------
        # WEB
        # ----------------------------------------------------

        if (
            self.live_web.get()
            or self.is_realtime(question)
        ):

            return "WEB_RESEARCH"

        # ----------------------------------------------------
        # KNOWLEDGE
        # ----------------------------------------------------

        if self.search_knowledge(question):

            return "KNOWLEDGE"

        # ----------------------------------------------------
        # OLLAMA
        # ----------------------------------------------------

        return "OLLAMA"

    # ========================================================
    # WEB SEARCH
    # ========================================================

    def web_search(self, question):

        try:

            from ddgs import DDGS

            results = []

            with DDGS() as ddgs:

                search_results = ddgs.text(
                    question,
                    max_results=6
                )

                for item in search_results:

                    results.append({

                        "title": item.get(
                            "title",
                            "Web Result"
                        ),

                        "url": item.get(
                            "href",
                            ""
                        ),

                        "snippet": item.get(
                            "body",
                            ""
                        )
                    })

            return results

        except Exception as error:

            raise RuntimeError(
                f"Web search failed: {error}"
            )

    # ========================================================
    # OLLAMA RESPONSE EXTRACTION
    # ========================================================

    def extract_ollama_content(self, response):

        if isinstance(
            response,
            str
        ):

            return response

        if isinstance(
            response,
            dict
        ):

            message = response.get(
                "message",
                {}
            )

            if isinstance(
                message,
                dict
            ):

                return message.get(
                    "content",
                    ""
                )

            return str(message)

        message = getattr(
            response,
            "message",
            response
        )

        if isinstance(
            message,
            str
        ):

            return message

        content = getattr(
            message,
            "content",
            None
        )

        if content is not None:
            return content

        return str(response)

    # ========================================================
    # OLLAMA BRAIN
    # ========================================================

    def ask_ollama(
        self,
        question,
        web_context=""
    ):

        memory_text = ""

        if self.memories:

            memory_text = (
                "\nMEMORY:\n"
                + "\n".join(
                    f"- {x}"
                    for x in self.memories
                )
            )

        system_prompt = """

You are TejaswiniGPT, a local AI Agent.

Your architecture contains:

GOAL
BRAIN
MEMORY
KNOWLEDGE
TOOLS
DECISION MAKING
ACTIONS
OUTPUT

You are running locally through Ollama.

Answer clearly and naturally.

Use a friendly, casual tone.

If web research information is provided,
use it to answer the user's question.

Do not invent facts that are not supported
by provided web research.

Reply in plain text.
"""

        prompt = (
            system_prompt
            + memory_text
            + "\n\nWEB RESEARCH:\n"
            + web_context
            + "\n\nUSER QUESTION:\n"
            + question
        )

        response = chat(

            model=OLLAMA_MODEL,

            messages=[

                {
                    "role": "system",
                    "content": system_prompt
                },

                {
                    "role": "user",
                    "content": prompt
                }
            ],

            stream=False
        )

        return self.extract_ollama_content(
            response
        )

    # ========================================================
    # STUDY BUDDY - AI GENERATOR
    # ========================================================

    def generate_study_content(
        self,
        topic
    ):

        prompt = f"""
    Create a fast study pack for this topic: {topic}

    The topic can be any subject. Adapt the content to it;
    do not assume it is computer networks.

    Return ONLY valid JSON with this structure:

{{
    "overview": "Exactly two paragraphs explaining the topic.",
    "quiz": [
        {{
            "question": "Question 1",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "answer": "Option A",
            "explanation": "Detailed explanation."
        }},
        {{
            "question": "Question 2",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "answer": "Option B",
            "explanation": "Detailed explanation."
        }},
        {{
            "question": "Question 3",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "answer": "Option C",
            "explanation": "Detailed explanation."
        }}
    ]
}}

Rules: exactly two overview paragraphs, exactly three
questions, exactly four options per question, one correct
answer, and an explanation for each answer. The answer
must exactly match one option. Return JSON only.
"""

        response = chat(

            model=OLLAMA_MODEL,

            messages=[

                {
                    "role": "system",
                    "content": (
                        "You generate strict JSON "
                        "educational content."
                    )
                },

                {
                    "role": "user",
                    "content": prompt
                }
            ],

            format="json",

            options={
                "temperature": 0.1,
                "num_predict": 700
            },

            keep_alive="5m",

            stream=False
        )

        content = self.extract_ollama_content(
            response
        )

        if not content:

            raise ValueError(
                "Ollama returned an empty response."
            )

        # Remove accidental code fences

        content = content.strip()

        content = re.sub(
            r"^```json\s*",
            "",
            content,
            flags=re.IGNORECASE
        )

        content = re.sub(
            r"^```\s*",
            "",
            content
        )

        content = re.sub(
            r"\s*```$",
            "",
            content
        )

        data = json.loads(
            content
        )

        overview = data.get(
            "overview",
            ""
        )

        quiz = data.get(
            "quiz",
            []
        )

        if not overview:

            raise ValueError(
                "No overview generated."
            )

        if not isinstance(
            quiz,
            list
        ) or len(quiz) != 3:

            raise ValueError(
                "Exactly 3 quiz questions are required."
            )

        for question in quiz:

            required = [
                "question",
                "options",
                "answer",
                "explanation"
            ]

            for key in required:

                if key not in question:

                    raise ValueError(
                        f"Missing quiz field: {key}"
                    )

            if len(
                question["options"]
            ) != 4:

                raise ValueError(
                    "Every question must have 4 options."
                )

            if question["answer"] not in question["options"]:

                raise ValueError(
                    "Correct answer does not match an option."
                )

        return overview, quiz

    # ========================================================
    # STUDY BUDDY START
    # ========================================================

    def start_study_from_button(self):

        topic = self.input_box.get().strip()

        if not topic:

            topic = ""

        self.open_study_buddy(
            topic
        )

    # ========================================================
    # STUDY BUDDY WINDOW
    # ========================================================

    def open_study_buddy(
        self,
        topic
    ):

        self.study_topic = topic

        self.study_stage = "topic_input"

        self.study_overview = ""

        self.study_quiz = []

        self.study_answers = []

        self.study_score = 0

        if self.study_window is not None:

            try:
                self.study_window.destroy()
            except Exception:
                pass

        self.study_window = tk.Toplevel(
            self.root
        )

        self.study_window.title(
            "📚 TejaswiniGPT Study Buddy"
        )

        self.study_window.geometry(
            "850x720"
        )

        self.study_window.minsize(
            700,
            600
        )

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        header = ttk.Frame(
            self.study_window,
            padding=15
        )

        header.pack(
            fill="x"
        )

        ttk.Label(
            header,
            text="📚 Study Buddy",
            font=(
                "Helvetica",
                23,
                "bold"
            )
        ).pack(
            anchor="w"
        )

        ttk.Label(
            header,
            text=f"Topic: {topic}"
        ).pack(
            anchor="w",
            pady=(3, 8)
        )

        self.study_stage_label = ttk.Label(
            header,
            text="Stage 1: topic_input"
        )

        self.study_stage_label.pack(
            anchor="w"
        )

        topic_frame = ttk.Frame(
            header
        )

        topic_frame.pack(
            fill="x",
            pady=(10, 0)
        )

        ttk.Label(
            topic_frame,
            text="Topic to study:"
        ).pack(
            side="left",
            padx=(0, 8)
        )

        self.study_topic_entry = ttk.Entry(
            topic_frame,
            font=(
                "Helvetica",
                12
            )
        )

        self.study_topic_entry.pack(
            side="left",
            fill="x",
            expand=True
        )

        self.study_topic_submit_button = ttk.Button(
            topic_frame,
            text="Submit Topic",
            command=self.generate_study_ui
        )

        self.study_topic_submit_button.pack(
            side="left",
            padx=(8, 0)
        )

        self.study_topic_entry.bind(
            "<Return>",
            lambda event: self.generate_study_ui()
        )

        if topic:
            self.study_topic_entry.insert(
                0,
                topic
            )

        # ----------------------------------------------------
        # Content
        # ----------------------------------------------------

        content_frame = ttk.Frame(
            self.study_window,
            padding=(15, 0, 15, 10)
        )

        content_frame.pack(
            fill="both",
            expand=True
        )

        self.study_content = tk.Text(
            content_frame,
            wrap="word",
            font=(
                "Helvetica",
                12
            ),
            padx=12,
            pady=12
        )

        study_scrollbar = ttk.Scrollbar(
            content_frame,
            orient="vertical",
            command=self.study_content.yview
        )

        self.study_content.configure(
            yscrollcommand=study_scrollbar.set
        )

        self.study_content.pack(
            side="left",
            fill="both",
            expand=True
        )

        study_scrollbar.pack(
            side="right",
            fill="y"
        )

        # ----------------------------------------------------
        # Bottom buttons
        # ----------------------------------------------------

        self.study_buttons = ttk.Frame(
            self.study_window,
            padding=10
        )

        self.study_buttons.pack(
            fill="x"
        )

        self.study_generate_button = ttk.Button(
            self.study_buttons,
            text="🧠 Submit Topic & Generate Quiz",
            command=self.generate_study_ui
        )

        self.study_generate_button.pack(
            side="left"
        )

        self.study_reset_button = ttk.Button(
            self.study_buttons,
            text="🔄 Reset",
            command=self.reset_study_buddy
        )

        self.study_reset_button.pack(
            side="right"
        )

        self.study_write(
            f"Topic: {topic}\n\n"
            "Stage 1: Topic Input\n\n"
            "Click 'Generate Study Material' "
            "to create focused study notes and a "
            "3-question MCQ quiz for any subject."
        )

    # ========================================================
    # STUDY BUDDY STAGE 1
    # ========================================================

    def generate_study_ui(self):

        topic = self.study_topic_entry.get().strip()

        if not topic:

            messagebox.showwarning(
                "Topic required",
                "Enter any topic you want to study."
            )

            return

        self.study_topic = topic

        self.study_generate_button.config(
            state="disabled"
        )

        self.study_topic_submit_button.config(
            state="disabled"
        )

        self.study_stage_label.config(
            text="Stage 1: topic_input → generating..."
        )

        self.study_write(
            "🧠 Ollama is generating your study material...\n\n"
            "Please wait..."
        )

        self.update_status(
            "📚 Study Buddy: Generating..."
        )

        def worker():

            try:

                overview, quiz = (
                    self.generate_study_content(
                        self.study_topic
                    )
                )

                self.root.after(
                    0,
                    lambda: self.study_generation_success(
                        overview,
                        quiz
                    )
                )

            except Exception as error:

                self.root.after(
                    0,
                    lambda: self.study_generation_error(
                        str(error)
                    )
                )

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    # ========================================================
    # GENERATION SUCCESS
    # ========================================================

    def study_generation_success(
        self,
        overview,
        quiz
    ):

        self.study_overview = overview

        self.study_quiz = quiz

        self.study_topic_entry.config(
            state="disabled"
        )

        self.study_stage = "quiz_active"

        self.study_stage_label.config(
            text="Stage 2: quiz_active"
        )

        self.show_quiz()

        self.update_status(
            "📝 Study Buddy: Quiz ready"
        )

    # ========================================================
    # GENERATION ERROR
    # ========================================================

    def study_generation_error(
        self,
        error
    ):

        self.study_stage = "topic_input"

        self.study_stage_label.config(
            text="Stage 1: topic_input"
        )

        self.study_generate_button.config(
            state="normal"
        )

        self.study_topic_submit_button.config(
            state="normal"
        )

        self.study_topic_entry.config(
            state="normal"
        )

        self.study_write(
            "❌ Study material generation failed.\n\n"
            f"Error:\n{error}\n\n"
            "Check that Ollama is running and the model "
            "is installed."
        )

        self.update_status(
            "● Agent Ready"
        )

    # ========================================================
    # STUDY BUDDY STAGE 2
    # ========================================================

    def show_quiz(self):

        self.study_content.configure(
            state="normal"
        )

        self.study_content.delete(
            "1.0",
            "end"
        )

        self.study_content.configure(
            state="disabled"
        )

        self.study_answer_vars = []

        # ----------------------------------------------------
        # Overview
        # ----------------------------------------------------

        self.study_write(
            "📖 STUDY NOTES\n\n"
            + self.study_overview
            + "\n\n"
            + "=" * 70
            + "\n\n"
            + "📝 INTERACTIVE QUIZ\n\n"
        )

        # ----------------------------------------------------
        # Questions
        # ----------------------------------------------------

        for index, question in enumerate(
            self.study_quiz,
            start=1
        ):

            self.study_write_append(
                f"{index}. {question['question']}\n\n"
            )

            variable = tk.StringVar(
                value=""
            )

            self.study_answer_vars.append(
                variable
            )

            for option in question["options"]:

                radio = ttk.Radiobutton(
                    self.study_content,
                    text=option,
                    variable=variable,
                    value=option
                )

                self.study_content.configure(
                    state="normal"
                )

                self.study_content.window_create(
                    "end",
                    window=radio
                )

                self.study_content.insert(
                    "end",
                    "\n"
                )

                self.study_content.configure(
                    state="disabled"
                )

            self.study_write_append(
                "\n"
            )

        # ----------------------------------------------------
        # Submit button
        # ----------------------------------------------------

        if hasattr(
            self,
            "study_submit_button"
        ):

            try:
                self.study_submit_button.destroy()
            except Exception:
                pass

        self.study_submit_button = ttk.Button(
            self.study_buttons,
            text="✅ Submit Quiz",
            command=self.grade_study_quiz
        )

        self.study_submit_button.pack(
            side="left",
            padx=(10, 0)
        )

        self.study_generate_button.pack_forget()

        self.update_status(
            "📝 Study Buddy: Quiz ready"
        )

    # ========================================================
    # STUDY BUDDY STAGE 3
    # ========================================================

    def grade_study_quiz(self):

        self.study_answers = [
            variable.get()
            for variable in self.study_answer_vars
        ]

        if any(
            not answer
            for answer in self.study_answers
        ):

            messagebox.showwarning(
                "Incomplete Quiz",
                "Please answer all 3 questions."
            )

            return

        self.study_score = 0

        for index, question in enumerate(
            self.study_quiz
        ):

            if (
                self.study_answers[index]
                == question["answer"]
            ):

                self.study_score += 1

        self.study_stage = "graded"

        self.study_stage_label.config(
            text="Stage 3: graded"
        )

        self.show_study_results()

        self.update_status(
            "🏆 Study Buddy: Quiz graded"
        )

    # ========================================================
    # STUDY RESULTS
    # ========================================================

    def show_study_results(self):

        self.study_content.configure(
            state="normal"
        )

        self.study_content.delete(
            "1.0",
            "end"
        )

        self.study_content.insert(
            "end",
            "🏆 FINAL QUIZ RESULTS\n\n"
        )

        self.study_content.insert(
            "end",
            f"Topic: {self.study_topic}\n\n"
        )

        self.study_content.insert(
            "end",
            f"FINAL SCORE: "
            f"{self.study_score}/3\n\n"
        )

        if self.study_score == 3:

            self.study_content.insert(
                "end",
                "🎉 Excellent! Perfect score!\n\n"
            )

        elif self.study_score == 2:

            self.study_content.insert(
                "end",
                "👍 Great job! Review the one incorrect answer.\n\n"
            )

        elif self.study_score == 1:

            self.study_content.insert(
                "end",
                "📚 Keep practicing. You can improve!\n\n"
            )

        else:

            self.study_content.insert(
                "end",
                "💪 Don't worry. Review the notes and try again!\n\n"
            )

        self.study_content.insert(
            "end",
            "=" * 70
            + "\n\n"
        )

        # ----------------------------------------------------
        # Detailed grading
        # ----------------------------------------------------

        for index, question in enumerate(
            self.study_quiz
        ):

            student_answer = (
                self.study_answers[index]
            )

            correct_answer = (
                question["answer"]
            )

            if student_answer == correct_answer:

                badge = "✅ PASS"

            else:

                badge = "❌ FAIL"

            self.study_content.insert(
                "end",
                f"{badge}\n"
            )

            self.study_content.insert(
                "end",
                f"Question {index + 1}:\n"
            )

            self.study_content.insert(
                "end",
                f"{question['question']}\n\n"
            )

            self.study_content.insert(
                "end",
                f"Your answer:\n"
                f"{student_answer}\n\n"
            )

            self.study_content.insert(
                "end",
                f"Correct answer:\n"
                f"{correct_answer}\n\n"
            )

            self.study_content.insert(
                "end",
                f"Explanation:\n"
                f"{question['explanation']}\n\n"
            )

            self.study_content.insert(
                "end",
                "-" * 70
                + "\n\n"
            )

        self.study_content.configure(
            state="disabled"
        )

        # ----------------------------------------------------
        # Remove submit
        # ----------------------------------------------------

        if hasattr(
            self,
            "study_submit_button"
        ):

            try:
                self.study_submit_button.destroy()
            except Exception:
                pass

        # ----------------------------------------------------
        # New topic button
        # ----------------------------------------------------

        self.study_new_topic_button = ttk.Button(
            self.study_buttons,
            text="📚 New Topic",
            command=self.reset_study_buddy
        )

        self.study_new_topic_button.pack(
            side="left"
        )

    # ========================================================
    # STUDY HELPERS
    # ========================================================

    def study_write(
        self,
        text
    ):

        self.study_content.configure(
            state="normal"
        )

        self.study_content.delete(
            "1.0",
            "end"
        )

        self.study_content.insert(
            "end",
            text
        )

        self.study_content.configure(
            state="disabled"
        )

    # --------------------------------------------------------

    def study_write_append(
        self,
        text
    ):

        self.study_content.configure(
            state="normal"
        )

        self.study_content.insert(
            "end",
            text
        )

        self.study_content.configure(
            state="disabled"
        )

    # ========================================================
    # STUDY RESET
    # ========================================================

    def reset_study_buddy(self):

        self.study_stage = "topic_input"

        self.study_topic = ""

        self.study_overview = ""

        self.study_quiz = []

        self.study_answers = []

        self.study_score = 0

        self.study_answer_vars = []

        if self.study_window is not None:

            try:
                self.study_window.destroy()
            except Exception:
                pass

        self.study_window = None

        self.update_status(
            "● Agent Ready"
        )

    # ========================================================
    # ACTION EXECUTION
    # ========================================================

    def execute_action(
        self,
        action,
        question
    ):

        # ----------------------------------------------------
        # STUDY BUDDY
        # ----------------------------------------------------

        if action == "STUDY_BUDDY":

            topic = re.sub(
                r"^(study buddy|study|quiz me on|quiz me|"
                r"create quiz on|create quiz|start quiz)\s*",
                "",
                question,
                flags=re.IGNORECASE
            ).strip()

            if not topic:

                topic = "Computer Science"

            self.open_study_buddy(
                topic
            )

            return (
                f"Opening Study Buddy for {topic}.",
                []
            )

        # ----------------------------------------------------
        # TIME
        # ----------------------------------------------------

        if action == "TIME":

            return (
                f"The current time in India is "
                f"{self.get_time()}.",
                []
            )

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        if action == "DATE":

            return (
                f"Today's date is "
                f"{self.get_date()}.",
                []
            )

        # ----------------------------------------------------
        # DAY
        # ----------------------------------------------------

        if action == "DAY":

            return (
                f"Today is "
                f"{self.get_day()}.",
                []
            )

        # ----------------------------------------------------
        # CALCULATOR
        # ----------------------------------------------------

        if action == "CALCULATOR":

            expression = re.sub(
                r"^(calculate|solve)\s+",
                "",
                question,
                flags=re.IGNORECASE
            )

            try:

                result = safe_calculate(
                    expression
                )

                return (
                    f"The answer is {result}.",
                    []
                )

            except Exception as error:

                return (
                    f"Calculation error: {error}",
                    []
                )

        # ----------------------------------------------------
        # MEMORY
        # ----------------------------------------------------

        if action == "MEMORY":

            memory = re.sub(
                r"^remember\s+",
                "",
                question,
                flags=re.IGNORECASE
            )

            self.remember(
                memory
            )

            return (
                "Got it! 🧠 I've saved that "
                "in my memory.",
                []
            )

        # ----------------------------------------------------
        # SHOW MEMORY
        # ----------------------------------------------------

        if action == "SHOW_MEMORY":

            if not self.memories:

                return (
                    "I don't have any saved memories yet.",
                    []
                )

            text = (
                "Here's what I remember:\n\n"
            )

            for memory in self.memories:

                text += (
                    f"• {memory}\n"
                )

            return (
                text,
                []
            )

        # ----------------------------------------------------
        # YOUTUBE
        # ----------------------------------------------------

        if action == "YOUTUBE":

            webbrowser.open(
                "https://youtube.com"
            )

            return (
                "Opening YouTube. ▶️",
                []
            )

        # ----------------------------------------------------
        # GOOGLE
        # ----------------------------------------------------

        if action == "GOOGLE":

            webbrowser.open(
                "https://google.com"
            )

            return (
                "Opening Google. 🌐",
                []
            )

        # ----------------------------------------------------
        # GITHUB
        # ----------------------------------------------------

        if action == "GITHUB":

            webbrowser.open(
                "https://github.com"
            )

            return (
                "Opening GitHub. 💻",
                []
            )

        # ----------------------------------------------------
        # MAC CALCULATOR
        # ----------------------------------------------------

        if action == "MAC_CALCULATOR":

            try:

                subprocess.Popen([
                    "open",
                    "-a",
                    "Calculator"
                ])

                return (
                    "Opening Calculator. 🧮",
                    []
                )

            except Exception as error:

                return (
                    f"Could not open Calculator: {error}",
                    []
                )

        # ----------------------------------------------------
        # TERMINAL
        # ----------------------------------------------------

        if action == "TERMINAL":

            try:

                subprocess.Popen([
                    "open",
                    "-a",
                    "Terminal"
                ])

                return (
                    "Opening Terminal. 💻",
                    []
                )

            except Exception as error:

                return (
                    f"Could not open Terminal: {error}",
                    []
                )

        # ----------------------------------------------------
        # KNOWLEDGE
        # ----------------------------------------------------

        if action == "KNOWLEDGE":

            return (
                self.search_knowledge(
                    question
                ),
                []
            )

        # ----------------------------------------------------
        # WEB RESEARCH
        # ----------------------------------------------------

        if action == "WEB_RESEARCH":

            try:

                results = self.web_search(
                    question
                )

            except Exception as error:

                return (
                    f"Web research error: {error}",
                    []
                )

            if not results:

                return (
                    "I couldn't find web results.",
                    []
                )

            context = ""

            for index, result in enumerate(
                results,
                start=1
            ):

                context += (
                    f"\nSOURCE {index}\n"
                    f"TITLE: {result['title']}\n"
                    f"URL: {result['url']}\n"
                    f"CONTENT: {result['snippet']}\n"
                )

            answer = self.ask_ollama(
                question,
                context
            )

            return (
                answer,
                results
            )

        # ----------------------------------------------------
        # NORMAL OLLAMA
        # ----------------------------------------------------

        if action == "OLLAMA":

            try:

                answer = self.ask_ollama(
                    question
                )

                return (
                    answer,
                    []
                )

            except Exception as error:

                return (
                    f"Ollama error: {error}",
                    []
                )

        return (
            "I don't know how to perform that action.",
            []
        )

    # ========================================================
    # DISPLAY SOURCES
    # ========================================================

    def show_sources(
        self,
        sources
    ):

        if not sources:
            return

        self.chat_box.configure(
            state="normal"
        )

        self.chat_box.insert(
            "end",
            "\n🔗 SOURCES\n"
        )

        for index, source in enumerate(
            sources,
            start=1
        ):

            title = source["title"]

            url = source["url"]

            self.chat_box.insert(
                "end",
                f"{index}. {title}\n"
            )

            start = self.chat_box.index(
                "end-1c"
            )

            self.chat_box.insert(
                "end",
                f"{url}\n"
            )

            end = self.chat_box.index(
                "end-1c"
            )

            tag = (
                f"link_{index}_{id(url)}"
            )

            self.chat_box.tag_add(
                tag,
                start,
                end
            )

            self.chat_box.tag_config(
                tag,
                underline=True
            )

            self.chat_box.tag_bind(
                tag,
                "<Button-1>",
                lambda event,
                link=url:
                webbrowser.open(link)
            )

            self.chat_box.insert(
                "end",
                "\n"
            )

        self.chat_box.insert(
            "end",
            "\n"
        )

        self.chat_box.configure(
            state="disabled"
        )

        self.chat_box.see(
            "end"
        )

    # ========================================================
    # MAIN AGENT LOOP
    # ========================================================

    def focus_input(self):

        self.input_box.focus_set()

        self.input_box.select_range(
            0,
            "end"
        )

    # --------------------------------------------------------

    def search_request(self):

        self.live_web.set(
            True
        )

        self.process_request()

    # --------------------------------------------------------

    def process_request(
        self,
        event=None
    ):

        question = (
            self.input_box
            .get()
            .strip()
        )

        if not question:
            return

        self.add_message(
            "You",
            question
        )

        self.input_box.delete(
            0,
            "end"
        )

        # ====================================================
        # GOAL
        # ====================================================

        goal = self.identify_goal(
            question
        )

        self.update_status(
            f"🎯 Goal: {goal}"
        )

        self.root.update()

        # ====================================================
        # BRAIN
        # ====================================================

        self.update_status(
            "🧠 Brain: Ollama..."
        )

        self.root.update()

        # ====================================================
        # DECISION
        # ====================================================

        action = self.decide_action(
            question
        )

        self.update_status(
            f"⚖️ Decision: {action}"
        )

        self.root.update()

        # ====================================================
        # ACTION
        # ====================================================

        self.update_status(
            f"⚡ Action: {action}"
        )

        self.root.update()

        try:

            answer, sources = (
                self.execute_action(
                    action,
                    question
                )
            )

        except Exception as error:

            answer = (
                f"Error while executing action: "
                f"{error}"
            )

            sources = []

        answer = self.clean_response(
            answer
        )

        # ====================================================
        # OUTPUT
        # ====================================================

        self.update_status(
            "💬 Output..."
        )

        self.add_message(
            APP_NAME,
            answer
        )

        if sources:

            self.show_sources(
                sources
            )

        self.update_status(
            "● Agent Ready"
        )

    # ========================================================
    # CLEAN RESPONSE
    # ========================================================

    def clean_response(
        self,
        response
    ):

        response = str(
            response
        ).strip()

        response = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            response
        )

        response = re.sub(
            r"^#{1,6}\s*",
            "",
            response,
            flags=re.MULTILINE
        )

        response = re.sub(
            r"[*`_~]",
            "",
            response
        )

        return response.strip()

    # ========================================================
    # STATUS
    # ========================================================

    def update_status(
        self,
        text
    ):

        self.status.config(
            text=text
        )

        self.root.update_idletasks()

    # ========================================================
    # CHAT MESSAGE
    # ========================================================

    def add_message(
        self,
        sender,
        message
    ):

        self.chat_box.configure(
            state="normal"
        )

        self.chat_box.insert(
            "end",
            f"{sender}:\n"
        )

        self.chat_box.insert(
            "end",
            f"{message}\n\n"
        )

        self.chat_box.configure(
            state="disabled"
        )

        self.chat_box.see(
            "end"
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = TejaswiniGPT(
        root
    )

    root.mainloop()