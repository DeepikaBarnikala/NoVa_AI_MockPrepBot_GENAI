
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY is missing from .env")
else:
    client = genai.Client(api_key=api_key)

    try:
        print("Testing Gemini connection...")

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents="Reply with exactly: NOVA is working!",
        )

        print("SUCCESS:")
        print(response.text or "Gemini returned an empty response.")

    except Exception as error:
        print("FAILED:")
        print(error)
