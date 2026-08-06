FROM python:3.10-slim

WORKDIR /app

# Instala dependências e configura DNS
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Configura DNS manualmente
RUN echo "nameserver 8.8.8.8" > /etc/resolv.conf
RUN echo "nameserver 8.8.4.4" >> /etc/resolv.conf

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]