import json
import pika
import requests
import time
from datetime import datetime, timezone

RABBITMQ_HOST = "rabbitmq"
RABBITMQ_USER = "user"
RABBITMQ_PASS = "pass"
QUEUE_NAME = "user_data"

def fetch_users(retries=3, delay=5):
    """
    Fetches 5 random user records from the API.
    Adds a UTC timestamp under the 'extracted.date' field.
    Retries if request fails.
    """
    for attempt in range(retries):
        try:
            response = requests.get("https://randomuser.me/api/?results=5", timeout=10)
            response.raise_for_status()
            data = response.json()

            if "results" not in data:
                raise ValueError("Invalid response: missing 'results'")

            for user in data["results"]:
                user["extracted"] = {"date": datetime.now(timezone.utc).isoformat()}

            return data["results"]

        except Exception as e:
            print(f"[Fetch Attempt {attempt + 1}] Error: {e}")
            time.sleep(delay)
    raise RuntimeError("Failed to fetch users after retries.")

def publish_to_queue(users):
    """
    Publishes user records to RabbitMQ queue as JSON messages.
    """
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)

    for user in users:
        try:
            message = json.dumps(user)
            channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=message)
            print("Sent user:", user.get("email", "no_email"))
        except Exception as e:
            print("Error sending message:", e)

    connection.close()

if __name__ == "__main__":
    while True:
        try:
            users = fetch_users()
            publish_to_queue(users)
            time.sleep(30)
        except Exception as e:
            print("Ingestion loop error:", e)
            time.sleep(15)