print("Hi! I am ChatBot. What is your name?")
name = input("You: ")
print("Nice to meet you, " + name + "! Type bye to leave.")
while True:
    message = input("You: ")    
    if message == "bye":
        print("ChatBot: Goodbye, " + name + "!")
        break
    elif message == "hello":
        print("ChatBot: Hello there!")
    elif message == "how are you":
        print("ChatBot: I am just code, but I feel great!")
    else:
        print("ChatBot: I am not sure how to answer that yet.")