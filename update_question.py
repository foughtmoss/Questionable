import os
import time
import random
import logging
import json
from dotenv import load_dotenv
from supabase import create_client
from google import genai
from google.genai.errors import ServerError, APIError
from datetime import date

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not API_KEY:
    raise Exception("La variabile GEMINI_API_KEY non è impostata.")
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise Exception("Variabili Supabase mancanti o non impostate.")

client = genai.Client(api_key=API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def generate_with_retry(model: str, prompt: str, max_retries: int = 5):
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
                wait = min(2 ** attempt + random.uniform(0, 1), 30)
                logging.warning(f"Modello sovraccarico (tentativo {attempt}). Riprovo tra {wait:.1f} secondi...")
                time.sleep(wait)
            else:
                logging.error(f"Errore del server: {e}")
                raise

        except APIError as e:
            logging.error(f"Errore API: {e}")
            raise

    raise Exception(f"Dopo {max_retries} tentativi, il modello non ha risposto.")


def get_scenario():
    scenarios = ["reale"]
    scenario = random.choice(scenarios)

    return scenario


def get_context():
    contexts = [
        "piccante", "infanzia", "imbarazzante", "amicizia", "provocatorio",
        "famiglia", "cringe", "università", "malizioso", "viaggio", "tabù",
        "vacanze", "cattivo", "sport", "controverso", "hobby", "vergognoso",
        "musica", "intimo", "film", "sospetto", "cibo", "codardo",
        "libri", "tradimento", "animali", "crush", "tempo libero",
        "vergogna scolastica", "sogni", "prima esperienza", "serie tv",
        "segreto mai confessato", "videogiochi", "desiderio nascosto",
        "tecnologia", "piacere proibito", "moda", "paura più grande",
        "cucina", "ossessione", "lavoro", "sesso", "crush nel gruppo",
        "weekend", "scuole superiori", "viaggio dei sogni", "routine mattutina",
        "amore"
    ]
    return random.choice(contexts)


def get_previous_questions(context, limit):
    response = supabase.table("questions") \
        .select("question") \
        .eq("context", context) \
        .execute()

    if response.data:
        if len(response.data) > limit:
            return [q['question'] for q in random.sample(response.data, limit)]
        else:
            return [q['question'] for q in response.data]

    return []


def build_prompt(context, previous_questions):
    scenario = get_scenario()
    print("-----SCENARIO-----")
    print(scenario)

    prompt = f"""
Sei un generatore creativo di una singola domanda per un gruppo di amici.
Il contesto in cui si inserisce la domanda, e che devi assolutamente rispettare, è: {context}.

Evita completamente i modelli di domande già usati.
Questi sono esempi di domande già fatte:
{previous_questions}

Requisiti per la domanda:
- Deve richiedere come risposta un nome presente nel gruppo.
- Può iniziare in modi diversi (es. "Chi", "Quale persona", "Cosa succederebbe", ecc.), NON usare sempre la stessa formula.
- Deve essere adatta ad un gruppo di 24enni, quindi deve rifarsi ad esperienze giovanili.
- Evita domande prevedibili o simili a quelle generate in precedenza.
- Lo scenario che devi assolutamente rispettare è: {scenario}.
- La domanda deve essere originale ma semplice.
- Non includere testo extra: genera solo la domanda, niente introduzioni o conclusioni.
- Non menzionare persone al di fuori del gruppo.
- Usa un linguaggio semplice.
- Non usare clichè come "alieni", "ambasciatore galattico".
- Evita di includere fatti personali o oggetti specifici che non puoi conoscere del gruppo
 (come i loro possedimenti, abitudini o la loro storia personale).
- La domanda deve contenere al massimo 300 caratteri.


Dopo aver generato la domanda, crea anche una  descrizione sintetica (max 20 parole) che riassuma il contenuto visivo principale della domanda. Questa descrizione sarà usata per generare un'immagine.

Requisiti per la descrizione:
- La descrizione deve essere in inglese.
- La descrizione deve essere un ottimo prompt per un modello text-to-image.
- La descrizione deve sottolineare che lo stile dell'immagine da generare deve essere "cinematic".
- La descrizione deve essere coerente con la domanda.
- La descrizione deve sottolineare che i soggetti hanno un'età compresa tra i 20 e i 24 anni.

Formatta l'output in JSON nel seguente modo, senza testo aggiuntivo:
{{
  "question": "testo della domanda qui",
  "image_prompt": "breve descrizione visiva qui"
}}
"""
    return prompt


def save_question(q: str, context: str, image_prompt: str):
    response = supabase.table("questions").insert({
        "question": q,
        "context": context,
        "created_at": date.today().isoformat(),
        "image_prompt": image_prompt
    }).execute()

    if hasattr(response, "status_code") and response.status_code != 201:
        raise Exception(f"Errore inserimento domanda su Supabase: {response.data}")

    print("Domanda salvata correttamente su Supabase.")


def clean_json_output(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        text = text.replace("json", "", 1).strip()
    return text


if __name__ == "__main__":
    context = get_context()
    print("\n--- CONTESTO ---")
    print(context)

    previous_questions = get_previous_questions(context=context, limit=10)
    print("\n--- DOMANDE PRECEDENTI ---")
    print(previous_questions)

    prompt = build_prompt(context, previous_questions)
    response = generate_with_retry("gemini-2.5-pro", prompt)
    print("\n--- RISPOSTA MODELLO ---")
    print(response)

    print("EXTRACTIN JSON")
    cleaned = clean_json_output(response)

    try:
        data = json.loads(cleaned)
        question = data.get("question", "").strip()
        image_prompt = data.get("image_prompt", "").strip()
    except json.JSONDecodeError:
        logging.error("Impossibile decodificare l'output JSON del modello.")
        question = response.strip()
        image_prompt = ""

    print("\n--- DOMANDA ---")
    print(question)
    print("\n--- PROMPT PER IMMAGINE ---")
    print(image_prompt)

    print("\n--- SALVATAGGIO DOMANDA NEL DB ---")
    save_question(question, context, image_prompt)
