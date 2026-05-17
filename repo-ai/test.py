from dotenv import load_dotenv
import os

from ibm_watsonx_ai.foundation_models import Model

# Load .env
load_dotenv()

# Read environment variables
API_KEY = os.getenv("WATSONX_API_KEY")
PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
URL = os.getenv("WATSONX_URL")
MODEL_ID = os.getenv("WATSONX_MODEL_ID")

print("\n=== ENV CHECK ===")
print("API KEY:", "FOUND" if API_KEY else "MISSING")
print("PROJECT ID:", PROJECT_ID)
print("URL:", URL)
print("MODEL:", MODEL_ID)

# Credentials
credentials = {
    "url": URL,
    "apikey": API_KEY
}

try:

    print("\n=== INITIALIZING MODEL ===")

    model = Model(
        model_id=MODEL_ID,
        credentials=credentials,
        project_id=PROJECT_ID
    )

    print("Model initialized successfully.")

    prompt = """
You are a senior software architect

Explain why circular dependencies are dangerous in large repositories.
"""

    print("\n=== GENERATING RESPONSE ===")

    response = model.generate_text(
        prompt=prompt
    )

    print("\n=== MODEL RESPONSE ===\n")

    print(response)

except Exception as e:

    print("\n=== ERROR ===\n")

    print(str(e))