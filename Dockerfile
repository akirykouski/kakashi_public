# Demo server for the change check. Build: docker build -t change-check . ; run: docker run -p 8000:8000 -e AI_GATEWAY_API_KEY=... change-check
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0 PORT=8000
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY core ./core
COPY ontology ./ontology
COPY data ./data
COPY rules_data ./rules_data
COPY web ./web
COPY tests/fixtures ./tests/fixtures
RUN useradd --create-home app && chown -R app /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/healthz')"
CMD ["python", "-m", "web.server"]
