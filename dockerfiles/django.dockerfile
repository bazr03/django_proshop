FROM python:3.8-alpine

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt .


RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /requirements.txt

RUN apk update \
    && apk add --virtual build-deps gcc python3-dev musl-dev \
    && apk add jpeg-dev zlib-dev libjpeg libwebp-dev \
    && apk add postgresql-dev  \
    && pip install Pillow \
    && apk del build-deps


WORKDIR /var/www
RUN mkdir djo_ecommerce

WORKDIR /var/www/djo_ecommerce
COPY ./app .
RUN adduser -D user
USER user



