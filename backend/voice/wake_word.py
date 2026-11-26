import pvporcupine
import pyaudio
import struct
import os

class WakeWordDetector:
    def __init__(self, keyword="jarvis", callback=None):
        self.access_key = os.environ.get("PICOVOICE_ACCESS_KEY", "")
        self.callback = callback
        
        # Initialize Porcupine wake-word engine
        self.porcupine = pvporcupine.create(
            access_key=self.access_key,
            keywords=[keyword]
        )
        self.pa = pyaudio.PyAudio()
        self.audio_stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )

    def listen_loop(self):
        print("[J.A.R.V.I.S. Voice] Wake-word detector active. Listening for 'Jarvis'...")
        try:
            while True:
                pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                
                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0:
                    print("[J.A.R.V.I.S. Voice] Wake-word DETECTED!")
                    if self.callback:
                        self.callback()
        except KeyboardInterrupt:
            self.cleanup()

    def cleanup(self):
        try:
            self.audio_stream.close()
        except Exception:
            pass
        try:
            self.porcupine.delete()
        except Exception:
            pass
        try:
            self.pa.terminate()
        except Exception:
            pass
