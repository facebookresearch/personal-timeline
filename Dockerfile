FROM python:3.10.4

WORKDIR ./app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY user_info.json .
COPY startup.sh .
RUN chmod 775 ./startup.sh
COPY ./src ./src

CMD ["/bin/bash", "-c", "./startup.sh"]