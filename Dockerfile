FROM node:22-slim AS web
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web ./
COPY contracts /app/contracts
RUN npx vite build

FROM python:3.13-slim
WORKDIR /app
COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt
COPY api api
COPY tests/fixtures tests/fixtures
COPY --from=web /app/web/dist web/dist
ENV REDRAFT_DATABASE_URL=sqlite:////data/redraft.db \
    REDRAFT_STORAGE_DIR=/data/files
VOLUME /data
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
