# Google Spreadsheet Reading and export with basic auth.

This parser will connect to a google spreadsheet that is shared with a service account, and with basic authentication returns the same google spreadsheet as a csv file. The purpose is to serve clients that use google spreadsheet feeds but cannot or will not publish them to the web because of security concerns. Only the first tab of the spreadsheet will be returned.

## How to set up a new customer for this service
1. Request the spreadsheet's id from the client for the feed in question.
  - the id is found in the url of the sheet (in below url 123abc123)
  - https://docs.google.com/spreadsheets/d/**123abc123**/edit#gid=1131221830
2. Ask the customer to share the spreadsheet with read-only access for this email: **smartly-gspreads@feeds-233607.iam.gserviceaccount.com** just like they would share the sheet with any other email address.
3. Create a secure password in 1Password. Hash the password using [this](https://argon2.online/) with a salt and default options.
4. Update secrets
  - Development
    - Follow the [instructions](https://smartlyio.atlassian.net/wiki/spaces/VULCAN/pages/19717477/Using+ejson+for+secrets) and add the below snippet of JSON with the spreadsheet id and hashed password you just created to `kubernetes/development/secrets.ejson`.
```
,\"SPREADSHEET_ID\":\"PASSWORD\"
```
  - Production
    - Go to [Vault](https://vault.smartly.io:8443/ui/vault/secrets/secret%2Fservice%2Ffeed-apps/show/gspread-feed-app-secrets/users.json) and [log in](https://smartlyio.atlassian.net/wiki/spaces/DEVOPS/pages/2977759235/Vault+Sync+to+Kube+Clusters+Production+services+secrets+sync)
    - Add the below snippet of JSON to the secrets with the spreadsheet id and hashed password you just created.
```
"SPREADSHEET_ID": "PASSWORD"
```
5. \[OPTIONAL\] If you are using a spreadsheet and would like to use a specific tab within the spreadsheet. Update the worksheets.json Mapping. Otherwise will default to the first tab in the spreadhsheet. 
  - Go to [Vault](https://vault.smartly.io:8443/ui/vault/secrets/secret%2Fservice%2Ffeed-apps/show/gspread-feed-app-secrets/worksheets.json) and [log in](https://smartlyio.atlassian.net/wiki/spaces/DEVOPS/pages/2977759235/Vault+Sync+to+Kube+Clusters+Production+services+secrets+sync)
  - Add the below snippet of JSON with the spreadsheet id and spreadsheet tab name (exactly as it is in the spreadsheet) to the worksheets.json file.
```
,\"SPREADSHEET_ID\":\"SPREADSHEET_TAB_NAME\"
```
6. Make sure not to delete any of the current users but just add the new one by copy pasting the old one to a text editor and add the new one there and copy paste it to a new version of the secret manager. **If you're unsure what you're doing, you can always ping your friends in TC.**
7. You can test that the feed works by sending a GET request or adding a feed to Smartly:

https://COMPANY_ID:PASSWORD@feed-apps.smartly.io/gspread-feed/?spreadsheet=SPREADSHEET_ID

## How does it work technically.

1. Call to the index page with the credentials and spreadsheet id as a paramteter.
2. Check the authentication matches the one setup in [Vault](https://vault.smartly.io:8443/ui/vault/secrets/secret%2Fservice%2Ffeed-apps/show/gspread-feed-app-secrets/users.json) and that the spreadsheet id matches the usr pw combination.
3. Returns the feed in a csv file.

## Security

We store the service account key in which the Gspread module authorizes with and the user/password data in [Vault](https://vault.smartly.io:8443/ui/vault/secrets/secret%2Fservice%2Ffeed-apps/show/gspread-feed-app-secrets/users.json).

## Running the app and tests

The app can be run locally in a python virtual environment or with Docker. The main benefit of the dockerized app is that instead of running the Flask development server,
it runs with the same Gunicorn setup as it does in production. It also removes the need to have the virtual environment up when running the tests or app.

When developing/testing `gspread-feed-app/Dockerfile` make sure `ENV GOOGLE_APPLICATION_CREDENTIALS=ExampleKeyFile.json` directs to the local path where you have stored the service account key file. If you do not have a service account key file, someone from Solutios Engineering can generate it for you.

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
