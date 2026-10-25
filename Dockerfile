FROM python:3.10-slim

# Instalar Java y dependencias de sistema
RUN apt-get update && apt-get install -y \
    default-jre-headless \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/default-java

WORKDIR /app

# Copiar e instalar librerías desde requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "limpieza.py"]