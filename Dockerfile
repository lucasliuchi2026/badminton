ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}

WORKDIR /app
COPY server/requirements.txt .
ARG PIP_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple
RUN pip install --no-cache-dir -i ${PIP_INDEX_URL} -r requirements.txt

COPY server/app ./app

ENV DATABASE_URL=sqlite:////data/badminton.db \
    UPLOAD_DIR=/data/uploads
EXPOSE 80

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-80}"]
