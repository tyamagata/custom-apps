# Example feed-apps app
Example app that can be used when creating a new parser in feed-apps.

## Features
- Setup for the Stackdriver logging used in feed-apps. See *Logging* for more info.
- Pre-configured docker-compose setup for running the Flask app and tests.
- Test examples that use the magical `pytest-flask` and `requests-mock` libraries.


## When creating a new app
- Copy this folder and name it `your-feed-parser-app`. The important part is the `-app` in the end as the folders with that appended will get deployed by the CI.
- Add a new image to `devbox.yml`.
  - Example config

```
  - name: aa-feed-from-catalog-app
    context: aa-feed-from-catalog-app
    dockerfile: Dockerfile
```

  - Example config for app with static files

```
  - name: weather-magic-app
    context: weather-magic-app
    dockerfile: Dockerfile
  - name: weather-magic-app-static
    context: weather-magic-app
    dockerfile: static.Dockerfile
```

- Update `kubernetes/{env}/apps.yml.erb`
  - Change `ingress_path` to reflect the name of your service so the final endpoint will be `https://feed-apps.smartly.io/{ingress_path}`. For clarity it's best to put the directory name without the `-app` part here, i.e. `your-feed-parser`.
  - *Optional*: If your service requires secrets,
    - Make sure to include `secrets_mount` and `env`. The secret values are mounted as json files and the name of the json files are passed as env vars.
    - Production secrets are managed with [Vault](https://vault.smartly.io:8443/)
      - Pick the OIDC login option
      - Type `generated-rbac-TEAM_NAME` in the Role field, where TEAM_NAME is the name of your team (in Workday) lower-cased and replace & with and
      - Sign in with Google
    - Update `kubernetes/development/secrets.ejson` for development secrets ([instructions](https://smartlyio.atlassian.net/wiki/spaces/VULCAN/pages/19717477/Using+ejson+for+secrets))
  - *Optional*: Change the resources to what's needed by the parser. Usually no changes are needed to these, so always start with the defaults.
  - Example config for production

```
<%= partial "app", app: {
  ingress_prefix: ingress_prefix,
  external_host: external_host,
  replicas: 3,
  name: "aa-feed-from-catalog-app",
  ingress_path: "aa-feed-from-catalog",
  requests_memory: "1Gi",
  readiness_period_seconds: 60,
  readiness_timeout_seconds: 8,
  liveness_period_seconds: 60,
  liveness_timeout_seconds: 8,
  secrets_mount: [ "aa-feed-from-catalog-app-secrets" ],
  env: [ { name:"SECRETS_PATH_CREDENTIALS",value:"/var/secrets/aa-feed-from-catalog-app-secrets/credentials.json" } ]
},
production: { }
          %>
```

- *Optional*: change the [Gunicorn worker](http://docs.gunicorn.org/en/stable/design.html#sync-workers) to what's required by the parser.
The currently used async worker `gevent` works for almost every case. But some cases may require for example the `eventlet` worker.
If you change the worker or other Gunicorn parameters, do it in `Dockerfile`.

## Running the app and tests
The recommended way to develop the app is to deploy it to devbox `devbox deploy` (Prerequisite: [devbox setup](https://github.com/smartlyio/devbox#getting-started))

The app can be run locally in a python virtual environment or with Docker. The main benefit of the dockerized app is that instead of running the Flask development server,
it runs with the same Gunicorn setup as it does in production. It also removes the need to have the virtual environment up when running the tests or app.

### Virtual environment
- Create and/or activate a Python 3.7 virtual environment for the app in your preferred way.
- If running for the first time or libraries are otherwise out of date: `pip install -r requirements.txt` (don't forget to `pip freeze > requirements.txt` if installing new libraries).
- **To run the tests**: `bin/test.sh` from the app's root folder.
- **To run the app**: `python app.py`

### Docker & docker-compose
- **To run the tests**: `docker-compose up test`
- **To run the app**: `docker-compose up app`
- Gunicorn needs a restart to reflect any changes made, and the easiest way to do that is to stop with CMD/CTRL + C and then run `docker-compose up app` again. 
- If it seems your changes didn't still get reflected, run with the `--build` flag, i.e. `docker-compose up --build app`

## Logging
The Stackdriver logging is configured into the Flask app object in app.py. 
- In app.py it can be used by calling the app.logger, for example `app.logger.info('Hello')`
- In other source files it can be used by importing `from Flask import current_app` and then using for example `current_app.logger.info('Hello')`
- The logger takes a dictionary in the `extra` argument for more logging info: `current_app.logger.warning('WARNING', extra={'issue': 'bad thing'})`
- **IMPORTANT**: When unit testing files that use the current_app.logger, remember to push the app context like in test_feedparser.py to avoid errors.
