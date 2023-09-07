# syntax=docker/dockerfile:1

FROM python:3.11

ARG FLASK_APP=membermatch/__init__.py

WORKDIR /code

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# ENTRYPOINT ["gunicorn", "main:app"]
ENTRYPOINT ["gunicorn", "membermatch/__init__.py:app"]
