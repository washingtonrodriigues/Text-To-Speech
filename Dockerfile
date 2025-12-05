FROM python:3.10-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório da aplicação
WORKDIR /app

# Instalar Python dependencies
RUN pip install --no-cache-dir \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
    TTS \
    fastapi \
    uvicorn[standard] \
    python-multipart

# Copiar código da aplicação
COPY api_xtts.py .

# Copiar arquivo de voz de referência (opcional)
COPY female_voice.opus* ./

# Expor porta
EXPOSE 8000

# Comando para executar
CMD ["python", "api_xtts.py"]
