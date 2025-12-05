FROM python:3.10

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libasound2-dev \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependências Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
    TTS \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    pydub

# Copiar arquivos
COPY api_xtts.py .
COPY female_voice.opus* ./

EXPOSE 8000

CMD ["python", "api_xtts.py"]
