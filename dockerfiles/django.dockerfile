FROM python:3.8-alpine


# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update \
    && apk add --virtual build-deps gcc python3-dev musl-dev \
    && apk add jpeg-dev zlib-dev libjpeg libwebp-dev \
    && apk add postgresql-dev  \
    && pip install Pillow \
    && apk del build-deps

RUN addgroup -S app && adduser -S app -G app


ENV APP_HOME=/home/app/web
RUN mkdir -p $APP_HOME
RUN mkdir -p $APP_HOME/staticfiles
WORKDIR $APP_HOME

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


COPY /app .
# RUN adduser -D user
RUN chown -R app:app $APP_HOME

USER app



