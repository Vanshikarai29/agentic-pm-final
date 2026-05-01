"""Run this to see which Gemini models are available on your API key."""
from dotenv import load_dotenv
load_dotenv()
import os
from google import genai

key = os.getenv("GEMINI_API_KEY")
print(f"API Key found: {bool(key)}")

client = genai.Client(api_key=key)

print("\nAvailable models:")
for m in client.models.list():
    print(f"  {m.name}")