FROM python:3.10-slim

WORKDIR /app

# Instala ffmpeg, libopus e utilitários de rede (para debug)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]