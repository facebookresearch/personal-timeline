FROM python:3.10.4

WORKDIR ./app
COPY requirements.txt .
COPY user_info.json .
COPY ./src ./src
RUN pip install -r requirements.txt

CMD ["python", "src/workflow.py"]