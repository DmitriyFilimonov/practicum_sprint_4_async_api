FROM python:3.10.0-slim

WORKDIR /opt/app

COPY requirements.txt requirements.txt

RUN  pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

CMD ["python", "-m","main", "--noinput"]