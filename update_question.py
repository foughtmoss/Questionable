import os
import time
import random
import logging
from dotenv import load_dotenv
from supabase import create_client
from google import genai
from google.genai.errors import ServerError, APIError
from datetime import date

# ----------------------------
# CONFIGURAZIONE LOGGING
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# ----------------------------
# CARICA VARIABILI D'AMBIENTE
# ----------------------------
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not API_KEY:
    raise Exception("La variabile GEMINI_API_KEY non è impostata.")
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise Exception("Variabili Supabase mancanti o non impostate.")

# ----------------------------
# INIZIALIZZA CLIENT
# ----------------------------

# Crea client genai
client = genai.Client(api_key=API_KEY)
# Crea client Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# ----------------------------
# FUNZIONE CON RETRY AUTOMATICO
# ----------------------------
def generate_with_retry(model: str, prompt: str, max_retries: int = 5):
    """Genera contenuto con retry automatico in caso di errore 503 o simile."""
    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"Tentativo {attempt}/{max_retries}...")
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            logging.info("Risposta ricevuta con successo.")
            return response.text

        except ServerError as e:
            if "overloaded" in str(e).lower() or "unavailable" in str(e).lower():
                wait = min(2 ** attempt + random.uniform(0, 1), 30)  # backoff esponenziale
                logging.warning(
                    f"Modello sovraccarico o non disponibile (tentativo {attempt}). "
                    f"Riprovo tra {wait:.1f} secondi..."
                )
                time.sleep(wait)
            else:
                logging.error(f"Errore del server: {e}")
                raise

        except APIError as e:
            logging.error(f"Errore API: {e}")
            raise

    raise Exception(f"Dopo {max_retries} tentativi, il modello non ha risposto.")


def get_context():
    contexts = [
        "piccante", "imbarazzante", "provocatorio", "cringe", "malizioso", "tabù",
        "cattivo", "controverso", "vergognoso", "intimo", "sospetto", "codardo",
        "tradimento", "crush", "vergogna scolastica", "prima esperienza",
        "segreto mai confessato", "desiderio nascosto", "piacere proibito",
        "paura più grande", "ossessione", "tabù sociale"
    ]
    return random.choice(contexts)


def get_previous_questions(limit):
    response = supabase.table("questions") \
        .select("question") \
        .execute()

    if response.data:
        if len(response.data) > limit:
            random_questions = random.sample(response.data, limit)
            return [q['question'] for q in random_questions]
        else:
            return [q['question'] for q in response.data]

    return []


def build_prompt(context, previous_questions):
    prompt = f"""
    Sei un generatore creativo di una singola domanda per un gruppo di amici.
    Il contesto in cui si inserisce la domanda è: {context}.

    Evita completamente i modelli di domande già usati.
    Questi sono esempi di domande già fatte:
    {previous_questions}

    Requisiti per la domanda:
    - Deve richiedere come risposta un nome presente nel gruppo.
    - Può iniziare in modi diversi (es. "Chi", "Quale persona", "Cosa succederebbe se", ecc.), NON usare sempre la stessa formula.
    - Evita domande prevedibili o simili a quelle generate in precedenza.
    - Puoi includere scenari ipotetici, accuse scherzose, situazioni assurde o puoi riferirti a scenari reali.
    - La domanda deve essere originale, stimolante e capace di sorprendere.
    - Non includere testo extra: genera solo la domanda, niente introduzioni o conclusioni.
    - Non menzionare persone al di fuori del gruppo.
    - La domanda deve essere contenere al massimo 300 caratteri.

    Ora genera una sola domanda originale, rispettando queste indicazioni.
    """
    return prompt


def save_question(q: str):
    response = supabase.table("questions").insert({
        "question": q,
        "created_at": date.today().isoformat()
    }).execute()

    if hasattr(response, "status_code") and response.status_code != 201:
        raise Exception(f"Errore inserimento domanda su Supabase: {response.data}")

    print("Domanda salvata correttamente su Supabase.")


# ----------------------------
# ESECUZIONE
# ----------------------------
if __name__ == "__main__":
    context = get_context()
    print("\n--- CONTESTO ---")
    print(context)

    previous_questions = get_previous_questions(limit=10)
    print("\n--- DOMANDE PRECEDENTI ---")
    print(previous_questions)

    prompt = build_prompt(context, previous_questions)
    question = generate_with_retry("gemini-2.5-pro", prompt)
    print("\n--- RISPOSTA MODELLO ---")
    print(question)

    print("\n--- SAVING QUESTION IN DB ---")
    save_question(question)
