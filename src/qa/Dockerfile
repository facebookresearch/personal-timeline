FROM python:3.10.4

WORKDIR /app

COPY src/requirements.txt .
RUN python -m pip install wheel setuptools pip --upgrade
RUN --mount=type=cache,target=/root/.cache \
    pip install -r requirements.txt

COPY src/qa/backend backend
COPY sample_data public/digital_data
COPY src/qa/server.py .

CMD ["python", "server.py"]
