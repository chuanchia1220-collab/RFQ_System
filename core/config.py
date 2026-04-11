import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GMAIL_USER = os.getenv("GMAIL_USER")
    GMAIL_PWD = os.getenv("GMAIL_PWD")
    TG_TOKEN = os.getenv("TG_TOKEN")
    TG_CHAT_ID = os.getenv("TG_CHAT_ID")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    @classmethod
    def validate(cls):
        missing = [k for k, v in cls.__dict__.items() if not k.startswith("_") and v is None and k != "validate"]
        if missing:
            raise ValueError(f"缺少環境變數: {missing}")
