FROM python:3.12-slim
WORKDIR /app
RUN python -m ensurepip --upgrade && pip install --upgrade pip
COPY ingest.py .
RUN pip install pika requests
CMD ["python", "-u", "ingest.py"]