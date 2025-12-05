import os
import tempfile
import base64
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
from TTS.api import TTS
import torch
from pydub import AudioSegment

class TTSRequest(BaseModel):
    text: str
    language: str = "pt"
    speaker_wav_base64: Optional[str] = None
    speed: float = 1.3

app = FastAPI(title="XTTS-v2 API", description="API para síntese de voz usando XTTS-v2")

# Cache do modelo
tts_model = None

def get_tts_model():
    """Carrega o modelo XTTS-v2 (lazy loading)"""
    global tts_model
    if tts_model is None:
        print("Carregando modelo XTTS-v2...")
        tts_model = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2").to("cpu")
        print("Modelo carregado com sucesso!")
    return tts_model

@app.get("/")
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "message": "XTTS-v2 API está funcionando",
        "endpoints": {
            "POST /tts": "Sintetizar voz a partir de texto",
            "POST /tts/upload": "Sintetizar voz com arquivo de referência uploadado"
        },
        "supported_languages": ["pt", "en", "es", "fr", "de", "it", "ja", "zh"]
    }

@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Sintetiza voz a partir de texto usando arquivo de referência em base64

    Parâmetros:
    - text: Texto a ser sintetizado
    - language: Idioma do texto (padrão: pt)
    - speaker_wav_base64: Arquivo de voz de referência em base64
    - speed: Fator de velocidade do áudio (padrão: 1.3)

    Exemplo de uso:
    curl -X POST "http://localhost:8000/tts" \
         -H "Content-Type: application/json" \
         -d '{
           "text": "Olá, este é um teste do XTTS-v2",
           "language": "pt",
           "speaker_wav_base64": "base64_encoded_audio_file",
           "speed": 1.3
         }'
    """
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="Texto é obrigatório")

        # Carregar modelo
        tts = get_tts_model()

        # Arquivo de referência
        speaker_wav_path = None
        if request.speaker_wav_base64:
            # Decodificar base64 e salvar temporariamente
            audio_data = base64.b64decode(request.speaker_wav_base64)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                speaker_wav_path = temp_file.name
        else:
            # Usar arquivo padrão se disponível
            default_speaker = "female_voice.opus"
            if os.path.exists(default_speaker):
                speaker_wav_path = default_speaker
            else:
                raise HTTPException(status_code=400, detail="Arquivo de voz de referência é obrigatório")

        # Arquivo de saída
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as output_file:
            output_path = output_file.name

        # Gerar áudio
        print(f"Gerando áudio para: '{request.text}'")
        tts.tts_to_file(
            text=request.text,
            speaker_wav=speaker_wav_path,
            language=request.language,
            file_path=output_path
        )

        # Limpar arquivo temporário de entrada
        if speaker_wav_path and speaker_wav_path != "female_voice.opus":
            os.unlink(speaker_wav_path)

        # Aplicar velocidade ao áudio
        audio = AudioSegment.from_wav(output_path)
        audio_rapido = audio.speedup(playback_speed=request.speed)

        # Salvar áudio final
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as final_file:
            final_path = final_file.name
        audio_rapido.export(final_path, format="wav")

        # Limpar arquivo temporário de saída original
        os.unlink(output_path)

        # Retornar arquivo de áudio
        return FileResponse(
            final_path,
            media_type="audio/wav",
            filename="output.wav",
            background=lambda: os.unlink(final_path)  # Limpar após envio
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar áudio: {str(e)}")

@app.post("/tts/upload")
async def text_to_speech_upload(
    text: str = Form(...),
    language: str = Form("pt"),
    speed: float = Form(1.3),
    speaker_file: UploadFile = File(...)
):
    """
    Sintetiza voz a partir de texto com arquivo de referência uploadado

    Parâmetros:
    - text: Texto a ser sintetizado
    - language: Idioma do texto (padrão: pt)
    - speed: Fator de velocidade do áudio (padrão: 1.3)
    - speaker_file: Arquivo de voz de referência

    Exemplo de uso:
    curl -X POST "http://localhost:8000/tts/upload" \
         -F "text=Olá, teste do XTTS-v2" \
         -F "language=pt" \
         -F "speed=1.3" \
         -F "speaker_file=@voz_referencia.wav"
    """
    try:
        if not text:
            raise HTTPException(status_code=400, detail="Texto é obrigatório")

        # Carregar modelo
        tts = get_tts_model()

        # Salvar arquivo de referência temporariamente
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            content = await speaker_file.read()
            temp_file.write(content)
            speaker_wav_path = temp_file.name

        # Arquivo de saída
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as output_file:
            output_path = output_file.name

        # Gerar áudio
        print(f"Gerando áudio para: '{text}'")
        tts.tts_to_file(
            text=text,
            speaker_wav=speaker_wav_path,
            language=language,
            file_path=output_path
        )

        # Limpar arquivo temporário de entrada
        os.unlink(speaker_wav_path)

        # Aplicar velocidade ao áudio
        audio = AudioSegment.from_wav(output_path)
        audio_rapido = audio.speedup(playback_speed=speed)

        # Salvar áudio final
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as final_file:
            final_path = final_file.name
        audio_rapido.export(final_path, format="wav")

        # Limpar arquivo temporário de saída original
        os.unlink(output_path)

        # Retornar arquivo de áudio
        return FileResponse(
            final_path,
            media_type="audio/wav",
            filename="output.wav",
            background=lambda: os.unlink(final_path)  # Limpar após envio
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar áudio: {str(e)}")

@app.get("/health")
async def health_check():
    """Verificação de saúde da API"""
    return {"status": "healthy", "model_loaded": tts_model is not None}

if __name__ == "__main__":
    # Executar servidor
    uvicorn.run(
        "api_xtts:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False
    )
