FROM mcr.microsoft.com/playwright/python:latest

WORKDIR /app

COPY backend ./backend

RUN pip install --no-cache-dir -r backend/requirements.txt \
    && python -m playwright install --with-deps chromium

ENV PORT=8000

WORKDIR /app/backend
CMD ["python", "server.py"]
