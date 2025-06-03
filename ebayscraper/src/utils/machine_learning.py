from llama_cpp import Llama
from pprint import pprint
import json
from ebayscraper.src.classes import Customer
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# unsloth/gemma-2-9b-it
# google/gemma-2-9b-it
# m1guelperez/gemma-2-9b-it-Q5_0-GGUF

messages = [
    {
        "role": "user",
        "content": "Du bist ein Assistent der Informationen aus Sätzen extrahiert welche eigenschaften von Inseraten beschreiben. "
        "Die Sätze müssen die Informationen 'Name', 'Preis', 'Stadt' und 'Radius' enthalten und diese müssen extrahier werden. Wenn eine der Informationen fehlt antworte nur 'None'. "
        "Alle weiteren Informationen können ignoriert werden. "
        "Die Informationen sollen in einem validen JSON-Format innerhalb von einer Antwort zurückgegeben werden. "
        "Beende deine Antwort immer mit +++.",
    },
    {
        "role": "assistant",
        "content": "Verstanden! Ich werde die Informationen als valides JSON-Format zurückgeben.",
    },
    {
        "role": "user",
        "content": "MacBook Pro 16 Zoll 2020, 16GB RAM, 512GB SSD, 5590 Euro, München, 50km",
    },
    {
        "role": "assistant",
        "content": '{"name": "MacBook Pro 16 Zoll 2020","preis": "5590","stadt": "München","radius": 50}+++',
    },
    {
        "role": "user",
        "content": "Suche nach einem iPhone 14 Pro Max, 256GB, 1200 Euro, Berlin, 30km",
    },
    {
        "role": "assistant",
        "content": "{'name': 'iPhone 14 Pro Max 256GB', 'preis': '1200', 'stadt': 'Berlin', 'radius': 30}+++",
    },
    {
        "role": "user",
        "content": "Ich möchte ein Samsung Galaxy S21 kaufen, Hamburg, 20km",
    },
    {
        "role": "assistant",
        "content": "None+++",
    },
    {
        "role": "user",
        "content": "Ich möchte ein Samsung Galaxy S21 kaufen, 800 Euro, Hamburg, 20km",
    },
    {
        "role": "assistant",
        "content": "'name': 'Samsung Galaxy S21', 'preis': '800', 'stadt': 'Hamburg', 'radius': 20}+++",
    },
    {
        "role": "user",
        "content": "Fernseher, 55 Zoll, 4K, 600 Euro, Köln, 40km",
    },
    {
        "role": "assistant",
        "content": "{'name': 'Fernseher 55 Zoll 4K', 'preis': '600', 'stadt': 'Köln', 'radius': 40}+++",
    },
    {
        "role": "user",
        "content": "Ich möchte ein Fahrrad kaufen, Mountainbike, 500 Euro, Frankfurt, 25km",
    },
    {
        "role": "assistant",
        "content": "{'name': 'Fahrrad Mountainbike', 'preis': '500', 'stadt': 'Frankfurt', 'radius': 25}+++",
    },
    {
        "role": "user",
        "content": "Ich suche nach einem Laptop, Dell XPS 13, 1000 Euro, Stuttgart",
    },
    {
        "role": "assistant",
        "content": "None+++",
    },
]

llm = Llama(
    model_path="./gemma-2-9b-it-q5_0.gguf",
    n_gpu_layers=-1,  # Use all available GPU memory
    verbose=False,
    n_ctx=2048,
    temperature=0.1,  # Lower temperature for more deterministic output
)


def extract_customer_values_with_ml(chat_id: int, chat_message: str) -> Customer | None:
    """
    Extracts the JSON content from the assistant's response.
    """
    messages.append(
        {
            "role": "user",
            "content": chat_message,
        }
    )
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=1024,
        stop=["+++"],  # Stop generation when '+++' is encountered
    )
    if "choices" not in response or len(response["choices"]) == 0:
        logger.error("No response from the model.")
        return None
    if str(response["choices"][0]["message"]["content"]).strip().removeprefix("+++") == "None":
        logger.error(
            f"Requested information is incomplete or not found for chat_id: {chat_id} with message: {chat_message}"
        )
        return None
    try:
        response_as_json = json.loads(
            str(response["choices"][0]["message"]["content"])
            .strip()
            .removesuffix("+++")
            .replace("'", '"')
        )
    except Exception as e:
        logger.error(f"Error when trying to convert to JSON: {e}")
        logger.error(
            f"Response content that led to an error: {response['choices'][0]['message']['content']}"
        )
        messages.pop()  # Remove the last user message in case of error
        return None

    messages.pop()  # Remove the last user message
    return Customer(
        chat_id=chat_id,
        item_name=response_as_json["name"].lower().strip(),
        price_limit=int(response_as_json["preis"]),
        location=response_as_json["stadt"].lower().strip(),
        radius=response_as_json["radius"],
    )
