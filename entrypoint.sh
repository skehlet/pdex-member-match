#!/bin/sh

export FLASK_APP=membermatch/__init__.py
export FLASK_RUN_PORT=8000
export FLASK_DEBUG=1
# flask run -p $FLASK_RUN_PORT
exec "$@"