from fastapi import Depends, HTTPException
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def get_openai_client() -> OpenAI:
    """
    Dependency to provide OpenAI client with API key from .env file.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured in .env file")
    return OpenAI(api_key=api_key)