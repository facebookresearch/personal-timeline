FROM python:3.10.4

WORKDIR /app

COPY src/requirements.txt .
RUN python -m pip install wheel setuptools pip --upgrade
RUN --mount=type=cache,target=/root/.cache \
    pip install -r requirements.txt

COPY src/frontend ./src/frontend
COPY src/common ./src/common
COPY src/__init__.py src/.

CMD ["python", "-m", "src.frontend.server"]