import os
from dotenv import load_dotenv

# Загружаем .env
load_dotenv(dotenv_path=".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}
