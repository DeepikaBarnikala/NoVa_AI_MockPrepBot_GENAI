
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY is missing from .env")
    raise SystemExit(1)

try:
    client = genai.Client(api_key=api_key)

    print("\nModels supporting text generation:\n")

    count = 0

    for model in client.models.list():
        actions = model.supported_actions or []

        if "generateContent" in actions:
            print(model.name)
            count += 1

    print(f"\nTotal models found: {count}")

except Exception as error:
    print("\nCould not retrieve models.")
    print("Technical details:", error)
