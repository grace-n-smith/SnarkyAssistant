import numpy as np
import pvporcupine
import pyaudio
import speech_recognition as sr
import struct
from threading import Thread
import time
import configparser
from queue import Queue

access_key = "xRu/WDprZ2VcFV8OUZ+HGpNwvkTHdPCajQM6u62bp6ImpqvmNnJDeA==" # AccessKey obtained from Picovoice Console (https://console.picovoice.ai/)

class AudioManager:
    l = None
    stop_rec = False
    display_man = None
    
    samps_stale = True
    current_samps = None

    output_queue = Queue()

    def __init__(self, logger, config_file, display_man, sound_man):
        # Porcupine handles the wakewords
        self.porc = pvporcupine.create(keywords=["computer"], access_key=access_key)
        self.fs = self.porc.sample_rate
        self.frame_len = self.porc.frame_length
        self.l = logger
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.parse_config()
        self.display_man = display_man
        self.sound_man = sound_man
        
        # Continuously collect samples in a separate thread, and make sure
        # they're always fresh before delivering them
        sample_thread = Thread(target = self.sample_loop)
        sample_thread.start()
        
        # Let things settle then baseline audio level for a bit
        baseline_samps = int(self.initial_thresh_time*self.fs)
        time.sleep(0.5)
        samps = self.get_samps(baseline_samps)
        self.base_level = self.rms(samps)
        self.l.log(f"Base RMS Level: {self.base_level}", "DEBUG")

        # Continuously wait for wakeword in this thread
        run_thread = Thread(target = self.run)
        run_thread.start()
        
    def sample_loop(self):
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=self.fs,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.frame_len)
        
        while not self.stop_rec:
            self.current_samps = \
                audio_stream.read(self.porc.frame_length,
                                  exception_on_overflow=False)
            self.samps_stale = False

        audio_stream.stop_stream()
        audio_stream.close()
        pa.terminate()

    def run(self):
        r = sr.Recognizer()
        self.l.log("Started to listen...", "RUN")
        wait_speech_nsamp = int(self.fs*self.wait_speech_buffer_time)
        transcription_nsamp = int(self.fs*self.transcription_buffer_time)
        current_nsamp = wait_speech_nsamp
        
        while not self.stop_rec:
            samps = self.get_samps_single()
            pcm = struct.unpack_from("h" * self.porc.frame_length, samps)
            keyword_index = self.porc.process(pcm)

            # If the wakeword was detected...
            if keyword_index >= 0:
                self.display_man.wakeword_detected()
                self.l.log("Wakeword Detected. Waiting for speech.", "RUN")
                self.sound_man.play_blocking("wakeword")
                
                # Continuously read samples until RMS value goes to baseline
                to_transcribe = []
                still_quiet = True
                while True:
                    samps = self.get_samps(current_nsamp)
                    if self.rms(samps) < self.dev_thresh*self.base_level \
                       and still_quiet:
                        continue
                    elif self.rms(samps) < self.dev_thresh*self.base_level:
                        current_nsamp = wait_speech_nsamp
                        break
    
                    if still_quiet:
                        current_nsamp = transcription_nsamp
                        self.display_man.talking_started()
                        self.l.log("You started talking!", "DEBUG")
                        still_quiet = False
                    
                    to_transcribe.append(samps)
    
                to_transcribe = np.hstack(to_transcribe)

                self.display_man.talking_finished()
                self.l.log("Done talking. Transcribing...", "DEBUG")
                audio = sr.AudioData(to_transcribe, self.fs, 2)
                try:
                    transcription = r.recognize_google(audio)
                    self.l.log(f"You said: {transcription}", "RUN")
                    self.output_queue.put(transcription)
                    self.display_man.transcription_finished(transcription)
                    self.sound_man.play_blocking("transcription success")
                except sr.UnknownValueError:
                    self.l.log("No audio found in segment", "DEBUG")
                    self.display_man.transcription_finished("")
                    self.sound_man.play_blocking("transcription failed")
                
            else:
                # Eventually implement continuous RMS updating here
                # with a list of past RMS values that gets averaged
                pass

    def stop(self):
        self.stop_rec = True

    def get_samps_single(self):
        while self.samps_stale:
            time.sleep(0.001)
        self.samps_stale = True
        return self.current_samps

    # Returns at least nsamp samps
    def get_samps(self,nsamp):
        all_vals = []
        total = 0
        while total < nsamp:
            samps = self.get_samps_single()
            samps = np.frombuffer(samps, dtype=np.int16)
            all_vals.append(samps)
            total = total+samps.size

        all_vals = np.hstack(all_vals)
        return all_vals
    
    def rms(self, samps):
        # We're using 16-bit integers, so want to cast to 64-bit before rms.
        # This caused me lots of headaches before realizing that the values
        # were overflowing...
        larger = np.array(samps, dtype=np.int64)
        return np.sqrt(np.mean(larger**2))

    def parse_config(self):
        self.transcription_buffer_time = \
            float(self.config["Audio"]["transcription_buffer_time"])
        self.wait_speech_buffer_time = \
            float(self.config["Audio"]["wait_speech_buffer_time"])
        self.dev_thresh = float(self.config["Audio"]["rms_deviation_thresh"])
        self.initial_thresh_time = \
            float(self.config["Audio"]["initial_thresh_time"])

