FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
COPY main.py .
COPY templates/ templates/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5099
CMD ["python", "main.py"]
