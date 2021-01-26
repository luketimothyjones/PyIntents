#!/usr/bin/env python

# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# --
# Imports for audio parsing
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from google.api_core import exceptions as google_exceptions

import pyaudio
from six.moves import queue

import time
import keyboard

# --
# File containing intent definitions and a built IntentionCollection
import voice_intents


# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk, keybind='shift+f9'):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True
        
        self._start_time = None
        self._released = False
        self._hotkey = None
        self._keybind = keybind

        
    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer
        )

        self.closed = False
        self._released = False
        self._start_time = time.time()
        
        self._hotkey = keyboard.add_hotkey(self._keybind, self._trigger_key_release, trigger_on_release=True)

        return self

        
    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()
        
        self._start_time = None
        keyboard.remove_hotkey(self._hotkey)

        
    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue
    
    
    def _trigger_key_release(self):
        self._released = True
        
        
    def generator(self):
        self._released = False
        
        # __exit__ not yet called, keybind is still held, timeout to prevent errors
        while not self.closed and not self._released and (time.time() - self._start_time) < 45:
            chunk = self._buff.get()
            if chunk is None:
                return
            
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while 1:
                try:
                    chunk = self._buff.get_nowait()
                    if chunk is None:
                        return
                    data.append(chunk)
                    
                except queue.Empty:
                    break
                
            yield b''.join(data)
        
# [END audio_stream]


class SafeResponseIterator:
    def __init__(self, unsafe):
        self.unsafe = unsafe
        
    def __iter__(self):
        while True:
            try:
                yield self.unsafe.__next__()
            
            except StopIteration:
                raise StopIteration
                
            except Exception as ex:
                print(f'Encountered exception:\n"{ex}"\n')
                return
                

def recognize_intent_loop(responses):
    for response in SafeResponseIterator(responses):
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue
        
        text = result.alternatives[0].transcript.lstrip()  # Won't know if it's a continuation!
        result = voice_intents.intentions.match(text)
        
        if not result:
            print(f'Sorry, I don\'t know how to help with "{text}"')
            

def google_speech_connector(keybind='shift+f12'):
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = 'en-US'  # a BCP-47 language tag

    client = speech.SpeechClient()
    
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code
    )
        
    streaming_config = types.StreamingRecognitionConfig(
        config=config,
        interim_results=False
    )

    while 1:
        keyboard.wait(keybind)
        
        with MicrophoneStream(RATE, CHUNK, keybind) as stream:
            audio_generator = stream.generator()
            
            requests = (types.StreamingRecognizeRequest(audio_content=chunk)
                        for chunk in audio_generator)

            responses = client.streaming_recognize(streaming_config, requests)

            # Now, put the transcription responses to use.
            recognize_intent_loop(responses)


if __name__ == '__main__':
    try:
        keybind = 'shift+f12'
        google_speech_connector(keybind)
        
    except KeyboardInterrupt:
        print("\nExiting...\n")
