FROM python:3.12-slim

WORKDIR /app

COPY transformer.py .

RUN python -m ensurepip --upgrade && pip install --upgrade pip \
    && pip install pika pandas pyarrow

CMD ["python", "-u", "transformer.py"]