import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # .env'yi yükler
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

resp = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Sadece 'Merhaba Burak' yaz."
)
print(resp.text)
