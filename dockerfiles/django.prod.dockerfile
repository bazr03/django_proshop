###########
# BUILDER #
###########

FROM python:3.8-alpine as builder
WORKDIR /var/www/djo_ecommerce
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update \
    && apk add --virtual build-deps gcc python3-dev musl-dev \
    && apk add jpeg-dev zlib-dev libjpeg libwebp-dev \
    && apk add postgresql-dev  \
    && pip install Pillow \
    && apk del build-deps

# lint
RUN pip install --upgrade pip
#RUN pip install flake8==3.9.2
COPY /app .
#RUN flake8 --ignore=E501,F401 .

# install dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /var/www/djo_ecommerce/wheels -r requirements.txt


##########
# FINAL #
##########
FROM python:3.8-alpine

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup -S app && adduser -S app -G app

# create the appropiate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
WORKDIR $APP_HOME

# install dependencies
RUN apk update && apk add libpq
COPY --from=builder /var/www/djo_ecommerce/wheels /wheels
COPY --from=builder /var/www/djo_ecommerce/requirements.txt .
RUN pip install --no-cache /wheels/* Pillow



COPY /app $APP_HOME

# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# change to the app user
USER app

