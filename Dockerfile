FROM python:3-alpine

# Note that git is not uninstalled later, as it's needed for the
#  installation of the requirements.
#
# PsycoPG is the driver for PostgreSQL installations
#  (used through SQLAlchemy.)
ADD requirements.txt /app/requirements.txt

RUN apk add --no-cache git libpq postgresql-dev build-base \
  && pip install -r /app/requirements.txt \
  && apk del git build-base postgresql-dev

ADD . /app
RUN pip install -e /app

# Bridge database (registrations, chatrooms, ...)
VOLUME /root/.local/share/plaza/bridges/twitter/db.sqlite

CMD programaker-twitter-service
