# BASE_IMAGE 可在本地构建时替换为加速镜像（平台构建用默认即可）
ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}

WORKDIR /app
COPY requirements.txt .
# PIP_INDEX_URL 可在平台构建时覆盖（国内/镜像加速场景）
ARG PIP_INDEX_URL=https://pypi.org/simple
RUN pip install --no-cache-dir -i ${PIP_INDEX_URL} -r requirements.txt

COPY app ./app

ENV DATABASE_URL=sqlite:////data/badminton.db \
    UPLOAD_DIR=/data/uploads \
    PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
