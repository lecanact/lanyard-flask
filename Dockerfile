FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production
ENV HTTP_PORT=4001

EXPOSE 4001

CMD ["python", "run.py"]
