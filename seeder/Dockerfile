FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN  pip install --upgrade pip \
    && pip install -r requirements.txt

COPY main.py .

CMD ["python", "-m","main", "--noinput"]
