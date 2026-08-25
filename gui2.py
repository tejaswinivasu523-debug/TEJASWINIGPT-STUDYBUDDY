import tkinter as tk
from tkinter import ttk


class TejaswiniGPT:
	def __init__(self, root):
		self.root = root
		self.root.title("TejaswiniGPT")
		self.root.geometry("520x420")
		self.root.minsize(360, 300)

		main = ttk.Frame(root, padding=18)
		main.pack(fill="both", expand=True)

		title = ttk.Label(main, text="TejaswiniGPT", font=("Helvetica", 22, "bold"))
		title.pack(anchor="w")

		subtitle = ttk.Label(main, text="A simple personal assistant")
		subtitle.pack(anchor="w", pady=(2, 14))

		self.chat = tk.Text(
			main,
			height=12,
			wrap="word",
			state="disabled",
			padx=12,
			pady=12,
			font=("Helvetica", 12),
		)
		self.chat.pack(fill="both", expand=True)

		input_frame = ttk.Frame(main)
		input_frame.pack(fill="x", pady=(14, 0))

		self.name_entry = ttk.Entry(input_frame, font=("Helvetica", 12))
		self.name_entry.pack(side="left", fill="x", expand=True)
		self.name_entry.insert(0, "Enter your name")
		self.name_entry.focus()
		self.name_entry.bind("<Return>", self.say_hello)

		submit_button = ttk.Button(input_frame, text="Submit", command=self.say_hello)
		submit_button.pack(side="left", padx=(8, 0))

	def add_message(self, speaker, message):
		self.chat.configure(state="normal")
		self.chat.insert("end", f"{speaker}: {message}\n\n")
		self.chat.configure(state="disabled")
		self.chat.see("end")

	def say_hello(self, _event=None):
		message = self.name_entry.get().strip()
		if not message or message == "Enter your name":
			self.add_message("TejaswiniGPT", "Please enter your name first.")
			return

		question = message.lower().rstrip("?!.,")
		responses = {
			"how are you": "I am doing great! Thank you for asking. What is your favorite color?",
			"what is your favorite color": "Blue is my favorite color. What is your favorite food?",
			"what is your favorite food": "That sounds interesting! What do you like to do for fun?",
			"what do you like to do for fun": "I like answering questions and chatting with you.",
			"thank you": "You are welcome! Thank you for chatting with TejaswiniGPT. Have a great day!",
			"thanks": "You are welcome! Thank you for chatting with TejaswiniGPT. Have a great day!",
			"hello": "Hello! How can I help you?",
			"hi": "Hi! How can I help you?",
		}

		self.add_message("You", message)
		response = responses.get(question, f"Hi, {message}!")
		self.add_message("TejaswiniGPT", response)
		self.name_entry.delete(0, "end")


if __name__ == "__main__":
	root = tk.Tk()
	TejaswiniGPT(root)
	root.mainloop()
