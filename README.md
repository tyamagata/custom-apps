
# Custom Apps

This a location for local custom applications which have a specific use case. These are either operational apps or just ideations and a work in progress. 

## Building a new app
Use one of the existing projects from here or the starting template to ensure the format stays the same. 

Checklist:
- The app lives in its own folder inside the `apps` folder.
- There's a requirements.txt with all dependencies.
- There's tests written in pytest.
- The code passes linting performed with [Flake8](https://flake8.pycqa.org/en/latest/) and [Black](https://black.readthedocs.io/en/stable/) based on the settings in the .flake8 file in the project root.
- Whatever you have defined in entrypoint of Dockerfile (probably gunicorn) is also in requirements.txt


## Virtual environments
Python applications can require specific versions of libraries. Virtual environments are used to create application-specific python configurations with a particular version of Python and additional packages.

There are several different ways to manage virtual environments. E.g. Python3 comes with venv. Whichever you end up using, make sure to generate a requirements.txt file so others can replicate your environment.

Note: Don't just copy requirements.txt from other apps! Otherwise, you'll end up with unnecessary dependencies.