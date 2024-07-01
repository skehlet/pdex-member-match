# README

## Launching

* Comment out the flask app in docker-compose.yml.
* Launch the Flask app manually with:

```bash
env \
    FLASK_APP=membermatch/__init__.py \
    FLASK_RUN_PORT=8000 \
    FLASK_DEBUG=1 \
    FHIR_STORE_SERVER=localhost \
    FHIR_STORE_PORT=8080 \
    flask run -p 8000
```

* Use Bruno to load data into the FHIR server at `localhost:8080`

* Check hello world with:

```sh
curl -vv localhost:8000
```

* Launch $member-match query with:

```sh
curl -vv 'localhost:8000/'
```

* I set up the Flash app to reverse proxy GET and POST requests to the backend FHIR server.
