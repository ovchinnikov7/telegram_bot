# syntax=docker/dockerfile:1
FROM python:3.8.10

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

WORKDIR /code
COPY . .

RUN pip install -r requirements.txt
