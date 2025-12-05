FROM python:3.10-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libasound2-dev \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV COQUI_TOS_AGREED=1

WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Atualizar pip
RUN pip install --upgrade pip

# Instalar PyTorch CPU + dependências
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Instalar restante
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "api_xtts.py"]
