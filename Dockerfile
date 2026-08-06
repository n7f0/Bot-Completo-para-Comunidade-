FROM python:3.10-slim

WORKDIR /app

# Instala dependências
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]