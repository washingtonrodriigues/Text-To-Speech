FROM python:3.10-slim

# Evita prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    libsndfile1 \
    && apt-get clean

# Criar diretório da app
WORKDIR /app

# Copiar arquivos
COPY requirements.txt .
COPY api_xtts.py .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Baixar o modelo XTTS-v2 ANTES do runtime
RUN python3 - << 'EOF'
from TTS.api import TTS
TTS("tts_models/multilingual/multi-dataset/xtts_v2")
EOF

EXPOSE 8000

CMD ["python3", "api_xtts.py"]
