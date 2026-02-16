
import asyncio
import base64
import json
import wave
import struct
from websockets.asyncio.client import connect
import pyaudio
from playsound3 import playsound
from concurrent.futures import CancelledError
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class gemini_audio:
    """
    Docstring for gemini_audio
    """
    def __init__(self,cleanup_event=None,on_connect=None):
            
        # ----- CONFIG -----
        self.API_KEY = os.environ.get("API_KEY")
        self.MODEL_ID = "gemini-2.5-flash-native-audio-preview-12-2025"
        self.WS_URI = (
            "wss://generativelanguage.googleapis.com/ws/"
            "google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent"
            f"?key={self.API_KEY}"
        )

        # 100 ms chunk at 16kHz, 16-bit mono: 16000 * 0.1 * 2 bytes = 3200 bytes
        self.CHUNK_MS = 100
        self.FORMAT = pyaudio.paInt16 
        self.CHANNELS = 1  
        self.CHUNK = 512 
        self.RATE = 16000 
        self.RECEIVE_SAMPLE_RATE = 24000
        self.output_user="reply.wav"
        self.user_input="question.wav"
        self.audio_queue=asyncio.Queue()
        self.ws = None
        self.on_connect = on_connect
        self.audio_output=asyncio.Queue()
        self.running = True
        self.cleanup_event = cleanup_event
        self.allow_interruptions = False
        # When True the model is currently sending audio; used to pause sending mic chunks
        self.is_model_speaking = False




    async def capture_audio(self):
        """Capture audio from your Mac's microphone and send to Gemini in realtime."""
        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )

            while True:
                try:
                    data = await asyncio.to_thread(stream.read, self.CHUNK, exception_on_overflow=False)
                    encoded_data = base64.b64encode(data).decode("utf-8")
                    realtime_input_msg = {
                        "realtime_input": {
                            "media_chunks": [
                                {
                                    "data": encoded_data,
                                    "mime_type": "audio/pcm;rate=16000"
                                }
                            ]
                        }
                    }
                    # If the model is speaking and we don't allow interruptions,
                    # skip sending microphone chunks to avoid overlap/crackle.
                    if self.is_model_speaking and not self.allow_interruptions:
                        await asyncio.sleep(0.01)
                        continue
                    await self.audio_queue.put(realtime_input_msg)
                except OSError as e:
                    print(f"Audio capture error: {e}")
                    await asyncio.sleep(0.1)  # Add small delay before retrying
                    continue

        except CancelledError:
            print("Audio capture cancelled")
        except Exception as e:
            print(f"Unexpected error in capture_audio: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()

    async def send_data(self):
            while True:
                data=await self.audio_queue.get()
                await self.ws.send(json.dumps(data))


    async def receive_server_messages(self):
            """reseved msg from server"""
            async for msg in self.ws:
                response = json.loads(msg)
                
                # If the server gave us audio data, store it for playback
                try:
                    parts = response["serverContent"]["modelTurn"]["parts"]
                    for p in parts:
                        if "inlineData" in p:
                            # This indicates audio data — model is speaking
                            self.is_model_speaking = True
                            audio_data_b64 = p["inlineData"]["data"]
                            audio_bytes = base64.b64decode(audio_data_b64)
                            self.audio_output.put_nowait(audio_bytes)
                        elif "text" in p:
                            # If the model also responds with text, you can process it here
                            print("Gemini text response:", p["text"])
                except KeyError:
                    pass

                # Check if the model ended its turn
                try:
                    turn_complete = response["serverContent"]["turnComplete"]
                    if turn_complete:
                        # Model finished speaking — clear speaking flag
                        self.is_model_speaking = False
                        # If the user interrupts or the turn is done, any leftover audio is ignored or cleared.
                        while not self.audio_queue.empty():
                            self.audio_queue.get_nowait()
                except KeyError:
                    pass




    async def play_responses(self):
            """Pull audio data from the queue and play it through speakers."""
            audio = pyaudio.PyAudio()
            stream = audio.open(
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.RECEIVE_SAMPLE_RATE,
                    output=True
            )

            try:
                while True:
                    audio_chunk = await self.audio_output.get()
                    await asyncio.to_thread(stream.write, audio_chunk)
            
            except CancelledError:
                   print("Playback cancelled")
            except Exception as e:
                   
                   print(f"[play_responses] {type(e).__name__}: {e}")

                   print(f"Unexpected error in play_responses: {e}")
            finally:
                    stream.stop_stream()
                    stream.close()
                    audio.terminate()


    async def main(self):
        """main func"""
        logger.info("Attempting to connect to Gemini at {self.WS_URI}")
        try:
            print(f"Connecting to: {self.MODEL_ID}")
            self.ws=await connect(self.WS_URI,additional_headers={"Content-Type": "application/json"})
            logger.info(" WebSocket connection established.")
            # 3) Setup (camelCase)
            logger.info(" Sending setup message.")
            setup_msg = {
                "setup": {
                    "model": f"models/{self.MODEL_ID}",
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {"voiceName": "Aoede"}
                            }
                        },
                    },
                    # Optional: give system instruction
                    "systemInstruction": {
                        "parts": [{"text": "You are a helpful and friendly AI personal assistant ."}]
                    },
                }
            }
            logger.info(" Waiting for setup response.")
            await self.ws.send(json.dumps(setup_msg))
            # Wait for setupComplete
            setup_resp = json.loads(await self.ws.recv())
            if "setupComplete" in setup_resp:
                print("Setup Accepted!")
            
            
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.capture_audio())
                tg.create_task(self.send_data())
                tg.create_task(self.receive_server_messages())
                tg.create_task(self.play_responses())


        except Exception as e:
            print(f"Error in Gemini connection: {e}")

if __name__ == "__main__":

    gemini=gemini_audio()
    asyncio.run(gemini.main())
