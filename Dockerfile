FROM python:2.7
MAINTAINER Marius Boeru <mboeru@gmail.com>

#install necessary dependencies
RUN apt-get update && apt-get -y install libffi-dev libssl-dev

ENV INSTALL_PATH /kodi-alexa
ENV GUNICORN_LOGLEVEL info
RUN mkdir -p $INSTALL_PATH

WORKDIR $INSTALL_PATH

#get latest
#RUN git clone https://github.com/m0ngr31/kodi-alexa.git .
COPY . $INSTALL_PATH

#install requirements
RUN pip install -r requirements.txt

CMD gunicorn --log-level $GUNICORN_LOGLEVEL -b 0.0.0.0:8000 alexa:app
