import os
import logging
import asyncio
from dotenv import load_dotenv
from supabase import create_client
from telegram import Bot

# ----------------------------
# CONFIGURAZIONE BASE
# ----------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
CHAT_ID = os.getenv("CHAT_ID")  # metti qui la chat ID del gruppo

if not TELEGRAM_BOT_TOKEN:
    raise Exception("Variabile TELEGRAM_BOT_TOKEN mancante nel file .env.")
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise Exception("Variabili Supabase mancanti nel file .env.")
if not CHAT_ID:
    raise Exception("CHAT_ID mancante nel file .env.")

# ----------------------------
# INIZIALIZZA SUPABASE
# ----------------------------
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


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


# ----------------------------
# CREA SONDAGGIO AUTOMATICO
# ----------------------------
async def create_poll():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    question = get_latest_question()

    if not question:
        logging.error("Nessuna domanda trovata nel database.")
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

    await bot.send_poll(
        chat_id=CHAT_ID,
        question=question,
        options=options,
        is_anonymous=False,
        allows_multiple_answers=False,
    )

    logging.info(f"Sondaggio creato con domanda: {question} e opzioni: {options}")


def main():
    logging.info("Bot Telegram avviato. Creazione automatica sondaggio...")
    asyncio.run(create_poll())
    logging.info("Sondaggio inviato. Spegnimento bot.")


if __name__ == "__main__":
    main()
