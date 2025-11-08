import os
import logging
import asyncio
from dotenv import load_dotenv
from supabase import create_client
from telegram import Bot
import requests

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
CHAT_ID = os.getenv("CHAT_ID")

CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
API_BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/"

if not TELEGRAM_BOT_TOKEN:
    raise Exception("Variabile TELEGRAM_BOT_TOKEN mancante nel file .env.")
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise Exception("Variabili Supabase mancanti nel file .env.")
if not CHAT_ID:
    raise Exception("CHAT_ID mancante nel file .env.")
if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
    raise Exception("CLOUDFLARE_ACCOUNT_ID o CLOUDFLARE_API_TOKEN mancanti nel file .env.")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

MODEL = "@cf/leonardo/lucid-origin"

headers = {
    "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
    "Content-Type": "application/json"
}

def generate_image(prompt: str):
    """
    Genera un'immagine usando il modello Cloudflare AI Lucid Origin.
    Restituisce i byte dell'immagine (utilizzabili da Telegram come `photo=image_data`).
    """

    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        logging.error("CLOUDFLARE_ACCOUNT_ID o CLOUDFLARE_API_TOKEN mancanti nel file .env.")
        return None

    payload = {"prompt": prompt}

    try:
        logging.info(f"Generazione immagine con prompt: '{prompt}'")
        response = requests.post(f"{API_BASE_URL}{MODEL}", headers=headers, json=payload)

        logging.info(f"Cloudflare AI status: {response.status_code}")

        if response.headers.get("Content-Type", "").startswith("image/"):
            return response.content

        try:
            data = response.json()
        except Exception as e:
            logging.error(f"Errore nel parsing JSON: {e}")
            logging.debug(response.text[:500])
            return None

        if "result" in data and "image" in data["result"]:
            import base64
            return base64.b64decode(data["result"]["image"])

        logging.error(f"Formato risposta inatteso: {data}")
        return None

    except Exception as e:
        logging.error(f"Errore nella generazione immagine: {e}")
        return None


def get_latest_question():
    response = (
        supabase.table("questions")
        .select("question")
        .order("id", desc=True)
        .limit(1)
        .execute()
    )

    if response.data and len(response.data) > 0:
        return response.data[0]["question"]
    return None


def get_latest_image_prompt():
    response = (
        supabase.table("questions")
        .select("image_prompt")
        .order("id", desc=True)
        .limit(1)
        .execute()
    )

    if response.data and len(response.data) > 0:
        return response.data[0]["image_prompt"]
    return None


async def create_poll():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    question = get_latest_question()

    if not question:
        logging.error("Nessuna domanda trovata nel database.")
        return

    image_prompt = get_latest_image_prompt()

    if not image_prompt:
        logging.error("Nessuna domanda trovata nel database.")
        return

    image_data = generate_image(image_prompt)

    if not image_data:
        logging.error("Errore nella generazione dell'immagine.")
        return

    bot_info = await bot.get_me()
    bot_name = bot_info.first_name

    admins = await bot.get_chat_administrators(CHAT_ID)

    options = [
        admin.user.first_name
        for admin in admins
        if not admin.user.is_bot and admin.user.first_name != bot_name
    ]

    if len(options) < 2:
        options.append("Nessun altro disponibile")

    await bot.send_photo(
        chat_id=CHAT_ID,
        photo=image_data,
        caption=question
    )
    logging.info("Immagine inviata con la domanda come didascalia.")

    await bot.send_poll(
        chat_id=CHAT_ID,
        question="Opzioni:",
        options=options,
        is_anonymous=False,
        allows_multiple_answers=True,
    )

    logging.info(f"Sondaggio creato con opzioni: {options}")


def main():
    logging.info("Bot Telegram avviato. Creazione automatica sondaggio...")
    asyncio.run(create_poll())
    logging.info("Sondaggio inviato. Spegnimento bot.")


if __name__ == "__main__":
    main()
