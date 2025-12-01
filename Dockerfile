FROM python:3.13.5-slim

WORKDIR /app

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
        pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "python" "./main.py"]