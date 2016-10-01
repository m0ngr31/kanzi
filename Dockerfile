FROM python:2.7-slim

# Based off of dockerfile found here:
# https://sebest.github.io/post/protips-using-gunicorn-inside-a-docker-image/

COPY . /

RUN pip install json-logging-py \
 && pip install -r /requirements.txt

EXPOSE 8000

CMD ["/usr/local/bin/gunicorn", "--config", "/gunicorn.conf", "--log-config", "/logging.conf", "-b", ":8000", "wsgi:application"]
