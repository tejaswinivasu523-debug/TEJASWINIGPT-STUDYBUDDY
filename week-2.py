# Week 2: Scoring, Dynamic Feedback & Forgiving Input

print("========================================")
print("    WELCOME TO QUIZ MASTER BOT v0.2    ")
print("========================================\n")

# Expanded Question Bank (Day 12)
questions = [
    {"question": "What is 2 + 2?", "answer": "4"},
    {"question": "What is the capital of Japan?", "answer": "Tokyo"},
    {"question": "How many days are in a week?", "answer": "7"},
    {"question": "What is 10 - 3?", "answer": "7"},
    {"question": "What color is the sky on a clear day?", "answer": "blue"},
    {"question": "What is 5 * 6?", "answer": "30"},
    {"question": "Which continent is India in?", "answer": "Asia"},
    {"question": "What is 12 / 4?", "answer": "3"}
]

score = 0  # Score counter (Day 8)

# Loop with question numbers (Day 13)
for index, item in enumerate(questions, start=1):
    # Forgiving input: converts to lowercase and strips outer spaces (Day 11)
    user_answer = input(f"Question {index} of {len(questions)}: {item['question']} ").lower().strip()
    correct_answer = item["answer"].lower().strip()
    
    if user_answer == correct_answer:
        print("Correct!\n")
        score += 1  # Increment score (Day 8)
    else:
        print(f"Wrong. The answer was {item['answer']}\n")

# Final score summary (Day 9)
print("=" * 40)
print(f"Quiz over! You scored {score} out of {len(questions)}")

# Reactive feedback messages (Day 10)
if score == len(questions):
    print("Perfect score! Amazing!")
elif score >= len(questions) / 2:
    print("Good job!")
else:
    print("Keep practising, you will get there!")
print("=" * 40)