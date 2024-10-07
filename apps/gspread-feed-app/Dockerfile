FROM python:3.11.3-slim
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV PIPENV_VENV_IN_PROJECT 1

RUN pip3 install pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install --deploy

COPY . /app
WORKDIR /app
ENV PATH="/.venv/bin:$PATH"

ENV PROMETHEUS_MULTIPROC_DIR /.prom_cache
RUN mkdir -p $PROMETHEUS_MULTIPROC_DIR

CMD ["gunicorn", "--config", "gunicorn.conf.py", "-t", "300", "-b", ":8080", "-k", "gevent", "-w", "3", "app:app"]
