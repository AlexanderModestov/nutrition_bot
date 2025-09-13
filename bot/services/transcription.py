import openai
from bot.config import Config
import logging
import os

async def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe audio file using OpenAI Whisper API
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        Transcribed text or empty string if failed
    """
    try:
        if not os.path.exists(audio_file_path):
            logging.error(f"Audio file not found: {audio_file_path}")
            return ""
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Open and transcribe the audio file
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        
        return transcript.strip() if transcript else ""
        
    except openai.APIError as e:
        logging.error(f"OpenAI API error during transcription: {e}")
        return ""
    except Exception as e:
        logging.error(f"Error transcribing audio: {e}")
        return ""

async def transcribe_audio_with_language(audio_file_path: str, language: str = None) -> dict:
    """
    Transcribe audio file with language detection and confidence
    
    Args:
        audio_file_path: Path to the audio file
        language: Optional language hint (e.g., 'en', 'ru')
        
    Returns:
        Dict with transcription, language, and other metadata
    """
    try:
        if not os.path.exists(audio_file_path):
            logging.error(f"Audio file not found: {audio_file_path}")
            return {"text": "", "language": "unknown", "confidence": 0.0}
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Prepare transcription parameters
        transcription_params = {
            "model": "whisper-1",
            "response_format": "verbose_json"
        }
        
        if language:
            transcription_params["language"] = language
        
        # Open and transcribe the audio file
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                **transcription_params
            )
        
        return {
            "text": transcript.text.strip() if transcript.text else "",
            "language": transcript.language or "unknown",
            "duration": transcript.duration or 0,
            "segments": transcript.segments if hasattr(transcript, 'segments') else []
        }
        
    except openai.APIError as e:
        logging.error(f"OpenAI API error during detailed transcription: {e}")
        return {"text": "", "language": "unknown", "confidence": 0.0}
    except Exception as e:
        logging.error(f"Error in detailed transcription: {e}")
        return {"text": "", "language": "unknown", "confidence": 0.0}