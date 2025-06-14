import base64
from dotenv import load_dotenv
import os

load_dotenv()

def encode_cookies(file_path):
    with open(file_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    print(f"YOUTUBE_COOKIES_B64={encoded}")

if __name__ == "__main__":
    encode_cookies(os.getenv("COOKIES_FILENAME"))