# ETL‑RandomUser

**ETL‑RandomUser** is a self‑contained, Docker‑orchestrated pipeline that:

1. **E**xtracts batches of fake users from the public API  
   <https://randomuser.me/api/?results=5>
2. **T**ransforms the raw payload into a clean business schema with basic
   data‑quality checks.
3. **L**oads each validated record to local storage (one file ≈ one row).

A **RabbitMQ** queue decouples ingestion from transformation, guaranteeing that
data is never lost even if a downstream container restarts.

The repository also ships a small reporting script that counts **male / female
users per country** across all processed files.

---

## Architecture & Flow

```text
┌──────────────┐   1. GET 5 users   ┌─────────────────────────────┐
│  Ingestion   │ ─────────────────► │ randomuser.me API (public) │
│  container   │                    └─────────────────────────────┘
│ (ingest.py)  │
└──────┬───────┘
       │ 2. publish JSON message / queue=user_data
┌──────▼───────┐
│ RabbitMQ     │  (durable buffer)
└──────┬───────┘
       │ 3. consume
┌──────▼───────┐   4. validate + reshape  ┌──────────────┐
│ Transformer  │ ────────────────────────►│   storage/   │
│ (transformer)│   5. save *.json         └──────────────┘
└──────────────┘


⸻

Repository Layout

etl-randomuser/
├─ docker-compose.yml     # orchestrates all services
├─ README.md              # ← you are here
│
├─ ingestion/
│   ├─ Dockerfile         # python:3.12‑slim + pika + requests
│   └─ ingest.py          # Extraction + publish to RabbitMQ
│
├─ transform/
│   ├─ Dockerfile         # python:3.12‑slim + pika + pandas/pyarrow
│   └─ transformer.py     # Validation, restructuring, loading
│
├─ storage/               # mounted volume – one JSON per user
│
└─ gender_stats.py        # CLI script to print gender counts


⸻

Prerequisites
	•	Docker Desktop ≥ v20
	•	docker‑compose plugin (bundled with modern Docker)
	•	(Optional) Python 3.9+ on the host if you want to run gender_stats.py
outside of a container.

⸻

Quick‑start (local workstation)

git clone https://github.com/Kxrma47/ETL-RandomUser.git
cd ETL-RandomUser/etl-randomuser

# 1. build & launch every service
docker compose up --build -d

# 2. follow logs (three terminals are handy)
docker compose logs -f ingestion
docker compose logs -f transform
docker compose logs -f rabbitmq

# 3. view output files
ls storage | head

# 4. on‑demand reporting
python gender_stats.py

To stop and remove everything:

docker compose down

To re‑build from scratch (e.g., after code changes):

docker compose down
docker compose build --no-cache
docker compose up -d


⸻

Service Details

Service	Image / Build	Role	Ports / Volumes
rabbitmq	rabbitmq:3-management	Message broker (AMQP)	5672, Web UI 15672
ingestion	custom (ingestion/Dockerfile)	Fetch 5 users every 30 s, push to user_data queue	—
transform	custom (transform/Dockerfile)	Listen to queue, validate & reshape, write file	binds ./storage:/app/storage
minio (optional)	minio/minio	S3‑compatible store (not yet wired)	9000, 9001

Data validation rules
	•	Mandatory fields: gender, name, location, email, dob, registered, phone, cell, id
	•	gender must be either male or female; anything else is rejected.
	•	Failed records are logged and skipped, pipeline keeps running.

Output schema (per file)

{
  "results": [
    {
      "gender": "female",
      "name":  { "title": "Ms", "first": "Lucy", "last": "Green" },
      "location": {
        "city": "London",
        "state": "Greater London",
        "country": "United Kingdom",
        "postcode": "E2 8DP"
      },
      "email": "lucy.green@example.com",
      "dob":        { "date": "...", "age": 28 },
      "registered": { "date": "...", "age": 5 },
      "phone": "071‑123‑4567",
      "cell":  "079‑987‑6543",
      "id":    { "name": "NIN", "value": "QQ 12 34 56 A" },
      "extracted": { "date": "2025‑05‑22T19:48:45.27Z" }
    }
  ]
}


⸻

Gender‑stats Utility

Run at any time to summarise gender distribution across all processed files:

python gender_stats.py

Sample output:

France:         2 male, 3 female
Brazil:         0 male, 3 female
Iran:           2 male, 2 female
...


⸻

Why JSON and not Parquet?

During local development and functional testing, readable JSON makes it
trivial to eyeball individual rows and debug the transformation logic. (its easy locally)

For production‑scale analytics, switching to Parquet is a single‑function
change (pyarrow.parquet.write_table). A skeleton dependency (pyarrow) is
already baked into the transform container for future upgrade.

⸻

Future things can be done
	•	MinIO integration – push Parquet files to S3‑compatible object store.
	•	Flask/Streamlit API – expose /gender‑stats endpoint.
	•	Grafana dashboard – visualise ingestion throughput & queue depth.
	•	CI with pytest – automated unit tests for fetch, transform & stats code.

⸻

Troubleshooting

Symptom	Fix
“command not found: docker”	Ensure Docker Desktop is installed, restart shell ($PATH).
Transformer stuck on “Waiting for RabbitMQ”	RabbitMQ still booting; the script retries 10× with 5 s delay.
No output from gender_stats.py	Verify files exist in storage/ and each contains the nested results list.


⸻

License

free to use, modify, and share.


