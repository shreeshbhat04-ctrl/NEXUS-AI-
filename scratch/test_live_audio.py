import asyncio
import os
from google import genai
from google.genai import types

api_key = os.getenv("GOOGLE_API_KEY")
model = "gemini-2.5-flash-native-audio-latest"

async def main():
    client = genai.Client(api_key=api_key)
    
    config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Puck"
                )
            )
        ),
        system_instruction=types.Content(parts=[types.Part(text="You are Nexus_ai, a helpful AI medical assistant. Keep your responses concise.")]),
        input_audio_transcription=types.AudioTranscriptionConfig()
    )
    
    print("Connecting to Gemini Live...")
    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            print("Connected successfully!")
            
            # Start a receive task
            async def receive_loop():
                try:
                    async for response in session.receive():
                        print(f"Received message: {response}")
                        if response.server_content:
                            parts = response.server_content.model_turn.parts if response.server_content.model_turn else []
                            for p in parts:
                                if p.inline_data:
                                    print(f"  Received audio chunk of size {len(p.inline_data.data)} bytes")
                except Exception as e:
                    print(f"Receive loop error: {e}")
            
            recv_task = asyncio.create_task(receive_loop())
            
            # Send 2 seconds of dummy silence audio (16kHz, 16-bit mono PCM = 32000 bytes/sec)
            print("Sending 2 seconds of dummy audio...")
            dummy_pcm = b"\x00" * 6400  # 0.2 seconds chunk
            for _ in range(10):
                await session.send_realtime_input(
                    audio=types.Blob(data=dummy_pcm, mime_type="audio/pcm;rate=16000")
                )
                await asyncio.sleep(0.2)
                
            print("Finished sending audio. Waiting for response...")
            await asyncio.sleep(5)
            recv_task.cancel()
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
