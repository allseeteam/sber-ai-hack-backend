FROM python:3.12

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY servers /app/

WORKDIR /app

CMD ["python", "websocket.py", "--host=0.0.0.0"]

