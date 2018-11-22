FROM python:3.6-slim

ENV PYTHONUNBUFFERED=1
ENV APP_DIR=/src

RUN mkdir $APP_DIR

WORKDIR $APP_DIR

ADD . $APP_DIR/

RUN pip install -r requirements.txt