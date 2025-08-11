# Usamos imagen base de Python
FROM python:3.11-slim

WORKDIR /app

# Copiamos código
COPY main.py .

# Instalamos dependencias
RUN pip install --no-cache-dir requests beautifulsoup4 google-cloud-storage

# Puerto por defecto para Cloud Run
ENV PORT 8080

# Ejecutamos la app con Gunicorn (opcional) o Flask simple con comando python main.py
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:main"]

