from gemini import chat_session

def chatbot():
    print("Welcome to the Gemini Chatbot! Type 'exit' to end the conversation.")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == 'exit':
            print("Chatbot: Goodbye!")
            break
        
        try:
            print("fetching......")
            response = chat_session.send_message(user_input)
            print("Chatbot:", response.text)
        except Exception as e:
            print("An error occurred:", str(e))

if __name__ == "__main__":
    chatbot()