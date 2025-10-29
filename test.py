# test.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Read your Gemini API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("❌ GEMINI_API_KEY is missing. Add it to your .env file.")

# Configure Gemini client
genai.configure(api_key=api_key)

# List available models
for model in genai.list_models():
    print(f"{model.name} | Supported methods: {model.supported_generation_methods}")
