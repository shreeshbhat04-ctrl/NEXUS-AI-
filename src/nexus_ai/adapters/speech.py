import logging

from google.cloud import speech
from google import genai
from google.genai import types
import wave
import io

from nexus_ai.config import get_settings

logger = logging.getLogger(__name__)

class GoogleSpeechAdapter:
    """Adapter for Google Cloud Speech-to-Text and Text-to-Speech API."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str | None = None) -> str:
        """Transcribe audio bytes using Google Cloud STT.
        
        It attempts to auto-detect the encoding (e.g. WebM/Opus from browsers) 
        and extract the transcript string.
        """
        # Instantiate the client using Google Cloud Application Default Credentials (ADC)
        # This prevents it from failing when expecting 'refresh_token' from workspace scopes.
        client = speech.SpeechClient()

        audio = speech.RecognitionAudio(content=audio_bytes)
        
        # Configure for common browser WebM/Ogg audio uploads
        # We rely on google-cloud-speech's ability to auto-detect WebM/Opus if headers match
        # WEBM_OPUS is the standard output of MediaRecorder across modern browsers
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code="en-US",
            enable_automatic_punctuation=True,
        )

        try:
            response = client.recognize(config=config, audio=audio)
            
            transcript_parts = []
            for result in response.results:
                transcript_parts.append(result.alternatives[0].transcript)
                
            full_transcript = " ".join(transcript_parts).strip()
            if not full_transcript:
                logger.warning("Google STT returned an empty transcript.")
            
            return full_transcript

        except Exception as e:
            logger.error("Speech to Text failed: %s", e)
            # Depending on platform, browsers might use different encodings like MP4 or LINEAR16,
            # If WebM/Opus fails, try letting Google auto-detect (works for FLAC, WAV, some others)
            logger.info("Attempting auto-detect fallback recognition...")
            fallback_config = speech.RecognitionConfig(
                language_code="en-US",
                enable_automatic_punctuation=True,
            )
            fallback_response = client.recognize(config=fallback_config, audio=audio)
            
            transcript_parts = []
            for result in fallback_response.results:
                transcript_parts.append(result.alternatives[0].transcript)
                
            return " ".join(transcript_parts).strip()

    def synthesize_speech(self, text: str) -> bytes:
        """Synthesize text into speech using Gemini 3.1 Flash TTS."""
        client = genai.Client(api_key=self.settings.google_api_key)
        try:
            response = client.models.generate_content(
                model='gemini-3.1-flash-tts-preview',
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=['AUDIO'],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name='Puck'
                            )
                        )
                    )
                )
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    pcm_data = part.inline_data.data
                    wav_io = io.BytesIO()
                    with wave.open(wav_io, 'wb') as wav_file:
                        wav_file.setnchannels(1)
                        wav_file.setsampwidth(2) # 16-bit
                        wav_file.setframerate(24000)
                        wav_file.writeframes(pcm_data)
                    return wav_io.getvalue()
            raise ValueError("No audio data returned by Gemini TTS")
        except Exception as e:
            logger.error("Gemini TTS failed: %s", e)
            return b""
