import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
os.environ["apiKey"] = GEMINI_API_KEY

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
PINECONE_INDEX = "murphy-plans"

SECRET_KEY = "murphy_v2_secret_key"
DEBUG = True