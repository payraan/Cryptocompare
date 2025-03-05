FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use port 8085 to avoid conflicts with other APIs
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8085"]
