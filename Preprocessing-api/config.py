from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    @classmethod
    def validate_settings(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")