FROM python:3.8

COPY requirements.txt .
RUN pip3 install -r requirements.txt

WORKDIR /app
ADD . /app

CMD python3 /app/core/run.py