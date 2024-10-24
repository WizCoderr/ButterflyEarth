import google.generativeai as genai

API_KEY = "AIzaSyC2-TALG6XNZGNtsHuX1XvkMJiLaBcOvC0"

# Configure the API key
genai.configure(api_key=API_KEY)

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="tunedModels/butterfly-earth-bjmed6b5pccr",
    generation_config=generation_config,
)

# Initialize the chat session
chat_session = model.start_chat(history=[])