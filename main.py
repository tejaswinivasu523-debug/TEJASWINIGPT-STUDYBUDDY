import tkinter as tk
from tkinter import ttk
from datetime import datetime
from zoneinfo import ZoneInfo

import json
import os
import re
import ast
import operator
import webbrowser
import subprocess

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
NOTES_FILE = "notes.txt"


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
        r"[0-9+\-*/().%\s]+",
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

            raise ValueError("Invalid number.")

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
# AGENT
# ============================================================

class TejaswiniGPT:

    def __init__(self, root):

        self.root = root

        self.root.title(APP_NAME)
        self.root.geometry("900x760")
        self.root.minsize(780, 620)
        self.root.configure(bg="#eef3ff")

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("App.TFrame", background="#eef3ff")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("Primary.TButton", background="#5b6cff", foreground="#ffffff", padding=(18, 10), font=("Helvetica", 10, "bold"))
        style.map("Primary.TButton", background=[("active", "#485cf0")], foreground=[("active", "#ffffff")])
        style.configure("Secondary.TButton", background="#edf2ff", foreground="#1f2937", padding=(14, 9), font=("Helvetica", 10, "bold"))
        style.map("Secondary.TButton", background=[("active", "#dfe7ff")], foreground=[("active", "#1f2937")])
        style.configure("Toggle.TCheckbutton", background="#eef3ff", foreground="#1f2937", font=("Helvetica", 10, "bold"))
        style.configure("Input.TEntry", fieldbackground="#f8fafc", foreground="#0f172a")

        # ----------------------------------------------------
        # MEMORY
        # ----------------------------------------------------

        self.memories = []
        self.load_memory()

        # ----------------------------------------------------
        # KNOWLEDGE
        # ----------------------------------------------------

        self.knowledge = {}
        self.load_knowledge()

        # ----------------------------------------------------
        # UI
        # ----------------------------------------------------

        main = tk.Frame(
            root,
            bg="#eef3ff",
            padx=18,
            pady=18
        )

        main.pack(
            fill="both",
            expand=True
        )

        header = tk.Frame(
            main,
            bg="#ffffff",
            highlightthickness=0,
            padx=18,
            pady=16
        )

        header.pack(
            fill="x",
            pady=(0, 12)
        )

        title = tk.Label(
            header,
            text=APP_NAME,
            font=("Helvetica", 27, "bold"),
            bg="#ffffff",
            fg="#111827",
            anchor="w"
        )

        title.pack(anchor="w")

        subtitle = tk.Label(
            header,
            text=(
                "Local AI Agent • Ollama • Memory • "
                "Knowledge • Tools • Web Research"
            ),
            font=("Helvetica", 10),
            bg="#ffffff",
            fg="#475569",
            anchor="w"
        )

        subtitle.pack(anchor="w", pady=(6, 0))

        self.status = tk.Label(
            header,
            text="● Agent Ready",
            bg="#e9f9ef",
            fg="#166534",
            font=("Helvetica", 10, "bold"),
            padx=10,
            pady=6,
            anchor="w"
        )

        self.status.pack(anchor="w", pady=(12, 0))

        pipeline = tk.Label(
            main,
            text=(
                "🎯 Goal → 🧠 Ollama → ⚖️ Decision → "
                "⚡ Action → 💬 Output"
            ),
            bg="#eef3ff",
            fg="#334155",
            font=("Helvetica", 10, "bold")
        )

        pipeline.pack(anchor="w", pady=(0, 10))

        chat_container = tk.Frame(
            main,
            bg="#ffffff",
            padx=12,
            pady=12
        )

        chat_container.pack(
            fill="both",
            expand=True
        )

        self.chat_box = tk.Text(
            chat_container,
            wrap="word",
            state="disabled",
            font=("Helvetica", 11),
            bg="#f8fafc",
            fg="#111827",
            padx=14,
            pady=14,
            relief="flat",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground="#dfe7ff",
            highlightcolor="#5b6cff",
            insertbackground="#111827"
        )

        scrollbar = ttk.Scrollbar(
            chat_container,
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

        self.chat_box.tag_configure(
            "user",
            foreground="#0f172a",
            font=("Helvetica", 11, "bold"),
            lmargin1=6,
            lmargin2=6,
            spacing1=4,
            spacing3=4
        )

        self.chat_box.tag_configure(
            "assistant",
            foreground="#1f2937",
            font=("Helvetica", 11),
            lmargin1=6,
            lmargin2=6,
            spacing1=4,
            spacing3=4
        )

        options = tk.Frame(
            main,
            bg="#eef3ff",
            pady=10
        )

        options.pack(
            fill="x"
        )

        self.live_web = tk.BooleanVar(
            value=False
        )

        tk.Checkbutton(
            options,
            text="Live Web Research",
            variable=self.live_web,
            bg="#eef3ff",
            fg="#1f2937",
            selectcolor="#e0e7ff",
            font=("Helvetica", 10, "bold")
        ).pack(
            side="left"
        )

        tk.Label(
            options,
            text="Search current information",
            bg="#eef3ff",
            fg="#64748b",
            font=("Helvetica", 10)
        ).pack(
            side="left",
            padx=(10, 0)
        )

        input_frame = tk.Frame(
            main,
            bg="#eef3ff",
            pady=(8, 0)
        )

        input_frame.pack(
            fill="x"
        )

        self.input_box = tk.Entry(
            input_frame,
            font=("Helvetica", 12),
            bg="#f8fafc",
            fg="#111827",
            insertbackground="#111827",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#dfe7ff",
            highlightcolor="#5b6cff",
            bd=0,
            padx=14,
            pady=12
        )

        self.input_box.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=4
        )

        search_button = ttk.Button(
            input_frame,
            text="Search",
            command=self.search_request,
            style="Secondary.TButton"
        )

        search_button.pack(
            side="left",
            padx=(8, 0)
        )

        submit = ttk.Button(
            input_frame,
            text="Send",
            command=self.process_request,
            style="Primary.TButton"
        )

        submit.pack(
            side="left",
            padx=(8, 0)
        )

        self.input_box.bind(
            "<Return>",
            self.process_request
        )

        self.input_box.focus()

        self.add_message(
            APP_NAME,
            (
                "Hello! 👋\n\n"
                "I am your local AI Agent powered by Ollama."
            )
        )

    # ========================================================
    # MEMORY
    # ========================================================

    def load_memory(self):

        if not os.path.exists(MEMORY_FILE):
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
                "knowledge, tools, decision making and "
                "actions."

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

        if "time" in q:
            return "Get current time."

        if "date" in q:
            return "Get current date."

        if "what day" in q:
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

        # TIME
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

        # DATE
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

        # DAY
        if any(
            x in q
            for x in [
                "what day",
                "which day",
                "what day is today"
            ]
        ):
            return "DAY"

        # CALCULATOR
        if (
            q.startswith("calculate ")
            or q.startswith("solve ")
        ):
            return "CALCULATOR"

        # MEMORY
        if q.startswith(
            "remember "
        ):
            return "MEMORY"

        if (
            "what do you remember" in q
            or "show memory" in q
        ):
            return "SHOW_MEMORY"

        # ACTIONS
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

        # WEB
        if (
            self.live_web.get()
            or self.is_realtime(question)
        ):
            return "WEB_RESEARCH"

        # KNOWLEDGE
        if self.search_knowledge(question):
            return "KNOWLEDGE"

        # OLLAMA
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

Reply in plain text only. Do not use Markdown,
asterisks, hashtags, backticks, tables, or
Markdown bullet points.

If web research information is provided,
use it to answer the user's question.

Do not invent facts that are not supported
by the provided web research.

When sources are provided, mention the
important source names in your answer.
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

        if isinstance(response, str):
            return response

        if isinstance(response, dict):
            message = response.get("message", {})

            if isinstance(message, dict):
                return message.get("content", "")

            return str(message)

        message = getattr(response, "message", response)

        if isinstance(message, str):
            return message

        return getattr(message, "content", str(message))

    # ========================================================
    # ACTION EXECUTION
    # ========================================================

    def execute_action(
        self,
        action,
        question
    ):

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

            self.remember(memory)

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

            text = "Here's what I remember:\n\n"

            for memory in self.memories:

                text += (
                    f"• {memory}\n"
                )

            return (
                text,
                []
            )

        # ----------------------------------------------------
        # WEBSITE ACTIONS
        # ----------------------------------------------------

        if action == "YOUTUBE":

            webbrowser.open(
                "https://youtube.com"
            )

            return (
                "Opening YouTube. ▶️",
                []
            )

        if action == "GOOGLE":

            webbrowser.open(
                "https://google.com"
            )

            return (
                "Opening Google. 🌐",
                []
            )

        if action == "GITHUB":

            webbrowser.open(
                "https://github.com"
            )

            return (
                "Opening GitHub. 💻",
                []
            )

        # ----------------------------------------------------
        # MAC ACTIONS
        # ----------------------------------------------------

        if action == "MAC_CALCULATOR":

            subprocess.Popen([
                "open",
                "-a",
                "Calculator"
            ])

            return (
                "Opening Calculator. 🧮",
                []
            )

        if action == "TERMINAL":

            subprocess.Popen([
                "open",
                "-a",
                "Terminal"
            ])

            return (
                "Opening Terminal. 💻",
                []
            )

        # ----------------------------------------------------
        # KNOWLEDGE
        # ----------------------------------------------------

        if action == "KNOWLEDGE":

            return (
                self.search_knowledge(question),
                []
            )

        # ----------------------------------------------------
        # WEB RESEARCH
        # ----------------------------------------------------

        if action == "WEB_RESEARCH":

            results = self.web_search(
                question
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

            answer = self.ask_ollama(
                question
            )

            return (
                answer,
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
            "\n� NEWS\n"
        )

        for index, source in enumerate(
            sources,
            start=1
        ):

            title = source.get("title", "News item")
            url = source.get("url", "")
            snippet = source.get("snippet", "")
            preview = snippet.strip() if snippet else "No summary available."

            self.chat_box.insert(
                "end",
                f"{index}. {title}\n"
            )

            start = self.chat_box.index(
                "end-1c"
            )

            self.chat_box.insert(
                "end",
                f"{preview}\n"
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
                underline=True,
                foreground="blue"
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

        self.chat_box.see("end")

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

        self.live_web.set(True)
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

        # =================================================
        # GOAL
        # =================================================

        goal = self.identify_goal(
            question
        )

        self.update_status(
            f"🎯 Goal: {goal}"
        )

        self.root.update()

        # =================================================
        # BRAIN
        # =================================================

        self.update_status(
            "🧠 Brain: Ollama..."
        )

        self.root.update()

        # =================================================
        # DECISION
        # =================================================

        action = self.decide_action(
            question
        )

        self.update_status(
            f"⚖️ Decision: {action}"
        )

        self.root.update()

        # =================================================
        # ACTION
        # =================================================

        self.update_status(
            f"⚡ Action: {action}"
        )

        self.root.update()

        result = self.execute_action(
            action,
            question
        )

        answer, sources = result

        answer = self.clean_response(
            answer
        )

        # =================================================
        # OUTPUT
        # =================================================

        self.update_status(
            "💬 Output..."
        )

        self.add_message(
            APP_NAME,
            answer
        )

        self.update_status(
            "● Agent Ready"
        )

    # ========================================================
    # UI
    # ========================================================

    def clean_response(
        self,
        response
    ):

        response = str(response).strip()

        response = re.sub(
            r"\[([^\]]+)\]\([^)]*\)",
            r"\1",
            response
        )

        response = re.sub(
            r"^\s{0,3}#{1,6}\s*",
            "",
            response,
            flags=re.MULTILINE
        )

        response = re.sub(
            r"^\s*(?:[-*+]\s+|\d+[.)]\s+)",
            "",
            response,
            flags=re.MULTILINE
        )

        response = re.sub(
            r"[`*_~]",
            "",
            response
        )

        response = re.sub(
            r"^\s*[-=]{3,}\s*$",
            "",
            response,
            flags=re.MULTILINE
        )

        return response.strip()

    # --------------------------------------------------------

    def update_status(
        self,
        text
    ):

        self.status.config(
            text=text
        )

        self.root.update_idletasks()

    # --------------------------------------------------------

    def add_message(
        self,
        sender,
        message
    ):

        self.chat_box.configure(
            state="normal"
        )

        tag = "assistant" if sender != "You" else "user"

        self.chat_box.insert(
            "end",
            f"{sender}:\n",
            tag
        )

        self.chat_box.insert(
            "end",
            f"{message}\n\n",
            tag
        )

        self.chat_box.configure(
            state="disabled"
        )

        self.chat_box.see("end")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = TejaswiniGPT(
        root
    )

    root.mainloop()