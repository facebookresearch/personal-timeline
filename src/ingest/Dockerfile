FROM python:3.10.4

WORKDIR ./app

COPY src/requirements.txt .
RUN python -m pip install wheel setuptools pip --upgrade
RUN --mount=type=cache,target=/root/.cache \
    pip install -r requirements.txt

COPY src/ingest src/ingest
COPY src/common src/common
COPY src/__init__.py src/.

RUN chmod 775 src/ingest/ingestion_startup.sh
CMD ["/bin/bash", "-c", "src/ingest/ingestion_startup.sh"]