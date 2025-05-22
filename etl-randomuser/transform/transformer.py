import pika
import json
import os
import time
from datetime import datetime, timezone

# RabbitMQ and storage configuration
RABBITMQ_HOST = "rabbitmq"
RABBITMQ_USER = "user"
RABBITMQ_PASS = "pass"
QUEUE_NAME = "user_data"
OUTPUT_DIR = "/app/storage"


os.makedirs(OUTPUT_DIR, exist_ok=True)

def transform_user(user):
    """
    Transforms and validates raw user data into the required schema.
    Ensures mandatory fields are present and gender is valid.
    Returns a dictionary nested under 'results', or None if invalid.
    """
    try:

        required_fields = ["gender", "name", "location", "email", "dob", "registered", "phone", "cell", "id"]
        for field in required_fields:
            if field not in user or user[field] is None:
                raise ValueError(f"Missing required field: {field}")

        if user["gender"] not in ["male", "female"]:
            raise ValueError("Invalid gender value")


        extracted_date = user.get("extracted", {}).get("date", datetime.now(timezone.utc).isoformat())


        transformed = {
            "results": [{
                "gender": user["gender"],
                "name": user["name"],
                "location": {
                    "city": user["location"].get("city"),
                    "state": user["location"].get("state"),
                    "country": user["location"].get("country"),
                    "postcode": user["location"].get("postcode"),
                },
                "email": user["email"],
                "dob": user["dob"],
                "registered": user["registered"],
                "phone": user["phone"],
                "cell": user["cell"],
                "id": user["id"],
                "extracted": {"date": extracted_date}
            }]
        }

        return transformed

    except Exception as e:
        print("Transformation error:", e)
        return None

def save_user(user_data):
    """
    Saves transformed user data to a JSON file with timestamped filename.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    filename = f"user_{timestamp}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(user_data, f, indent=2)
    print("Saved:", filename)

def callback(ch, method, properties, body):
    """
    Callback for handling incoming messages from RabbitMQ.
    Applies transformation and saves to storage.
    """
    try:
        user = json.loads(body)
        transformed = transform_user(user)
        if transformed:
            save_user(transformed)
        else:
            print("Skipped invalid user record.")
    except Exception as e:
        print("Callback error:", e)

def wait_for_rabbitmq(host, credentials, retries=10, delay=5):
    """
    Waits for RabbitMQ to be available, retries with delay if not.
    """
    for i in range(retries):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=credentials))
            connection.close()
            print("RabbitMQ is ready!")
            return
        except Exception as e:
            print(f"Waiting for RabbitMQ ({i+1}/{retries})... Error: {e}")
            time.sleep(delay)
    raise Exception("RabbitMQ not available after retries")

def main():
    """
    Entry point. Connects to RabbitMQ, consumes messages, and triggers transformation.
    """
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    wait_for_rabbitmq(RABBITMQ_HOST, credentials)

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)

    print("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    main()