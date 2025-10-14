FROM python:3.11-slim

WORKDIR /TIA_Smart_chat_v3

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

COPY .env .env

EXPOSE 8080

ENV PYTHONPATH=/TIA_Smart_chat_v3
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "TIA_Smart_chat_v3.main:app", "--host", "0.0.0.0", "--port", "8080"]