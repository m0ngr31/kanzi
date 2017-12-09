FROM python:2.7-slim
LABEL maintainer="Tomas Kislan kislan.tomas@gmail.com"

ENV INSTALL_PATH /kodi-alexa
ENV CONFIG_DIR /config
ENV GUNICORN_LOGLEVEL info
RUN mkdir -p $INSTALL_PATH

WORKDIR $INSTALL_PATH

COPY . $INSTALL_PATH

#install requirements
RUN apt-get update && apt-get -y install libffi-dev libssl-dev gcc && \
  pip install -r requirements.txt  && \
  pip install python-Levenshtein && \
  apt-get -y remove gcc && \
  apt-get -y autoremove

EXPOSE 8000

ENTRYPOINT gunicorn --log-level $GUNICORN_LOGLEVEL -b 0.0.0.0:8000 alexa:app
