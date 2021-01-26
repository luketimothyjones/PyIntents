import sys
import time
from queue import Queue, Empty

# Pythonnet configuration
sys.path.append('./DotNET/')

import clr  # Allow importing of .NET modules (import pythonnet)
clr.AddReference('System')
clr.AddReference('System.Speech')
clr.AddReference('System.Globalization')


import System
import System.Speech.Recognition as Recognition
import System.Globalization as Globalization

import System.Speech.Synthesis as Synthesis

from System import InvalidOperationException


# --
# File containing intent definitions and a built IntentionCollection
import voice_intents


class Recognizer:

    def __init__(self, trigger='start listening', locale="en-us",
                 hypoHandler=None, acceptHandler=None, rejectHandler=None,
                 minConfidence=.7):
                 
        self._min_confidence = minConfidence
        
        self._culture = Globalization.CultureInfo(locale)
        self._engine = Recognition.SpeechRecognitionEngine()

        # Load trigger word
        trigger_builder = Recognition.GrammarBuilder('start listening')
        trigger_grammer = Recognition.Grammar(trigger_builder)
        self._engine.LoadGrammar(trigger_grammer)
        
        # Load rest of language
        self._engine.LoadGrammar(Recognition.DictationGrammar())
        
        # Add handlers
        self._engine.SpeechHypothesized        += self._hypothesized_handler
        self._engine.SpeechRecognized          += self._recognized_handler
        self._engine.SpeechRecognitionRejected += self._rejected_handler

        self._engine.SetInputToDefaultAudioDevice()
        
        """
        self._engine.InitialSilenceTimeout      = System.TimeSpan.FromSeconds(1)
        self._engine.BabbleTimeout              = System.TimeSpan.FromSeconds(1)
        self._engine.EndSilenceTimeout          = System.TimeSpan.FromSeconds(1)
        self._engine.EndSilenceTimeoutAmbiguous = System.TimeSpan.FromSeconds(1.5)
        """
        
        self.hypothezied_queue = Queue()    
        self.recognized_queue  = Queue()
        self.rejected_queue    = Queue()

        
    def listen_once(self, attempts=2):
        attempt_count = 0
        
        while attempt_count < attempts:
            try:
                self._engine.RecognizeAsync(Recognition.RecognizeMode.Single)
                return
                
            except InvalidOperationException:
                time.sleep(.1)
                attempt_count += 1
        
        
    def emulate_recognize(self, inp):
        self._engine.EmulateRecognize(inp, Globalization.CompareOptions.IgnoreCase)
        
    def emulate_recognize_async(self, inp):
        self._engine.EmulateRecognizeAsync(inp, Globalization.CompareOptions.IgnoreCase)
    
    
    def _acceptable(self, result):
        return result.Confidence >= self._min_confidence

        
    def _hypothesized_handler(self, _, event_args):
        result = event_args.Result
        
        if self._acceptable(result):
            self.hypothezied_queue.put_nowait(result.Text)
        
        
    def _recognized_handler(self, _, event_args):
        result = event_args.Result
        
        if self._acceptable(result):
            self.recognized_queue.put_nowait(result.Text)
        
        
    def _rejected_handler(self, _, event_args):
        result = event_args.Result
        alternates = result.Alternates
        acceptable = [a.Text for a in alternates if self._acceptable(a) and a.Text != '']
        
        if len(acceptable) > 0:
            self.recognized_queue.put_nowait(acceptable)
        
        
    def teardown(self):
        self._engine.RecognizeAsyncCancel()
        self._engine.Dispose()
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args, **kwargs):
        self.teardown()


# ================
class Synthesizer:
    
    def __init__(self, voice=False):
        self._engine = Synthesis.SpeechSynthesizer()

        if not voice:
            self.select_voice(self.get_installed_voices(True)[0])

    # ----
    def get_installed_voices(self, return_names=False):
        """
        Get the list of Windows Sythesis voices installed to the current machine
        
        return_names (bool) :: False (default) prints the list, True returns the list
        """

        installed = [v.VoiceInfo.Name for v in self._engine.GetInstalledVoices()]

        if return_names:
            return installed

        print(installed)

    # ----
    def select_voice(self, voice):
        self._engine.SelectVoice(voice)

    # ----
    def speak(self, phrase):
        self._engine.Speak(phrase)

    # ----
    def teardown(self):
        self._engine.Dispose()

    # ----
    def __enter__(self):
        return self

    def __exit__(self):
        self.teardown()


# ================
def recognize_loop():
    with Recognizer() as recognizer:
        try:
            while 1:
                elapsed = 0
                recognizer.listen_once()

                # Automatically restart recognizer every 8 seconds
                while elapsed < 8:
                    try:
                        text = recognizer.recognized_queue.get_nowait()
                        print(text)

                        result = voice_intents.intentions.match(text)
                        if not result:
                            print(f'Sorry, I don\'t know how to help with "{text}"')

                        break

                    except Empty:
                        time.sleep(.25)
                        elapsed += .25

        except KeyboardInterrupt:
            print('\nExiting...')
            return


# ----
if __name__ == '__main__':
    recognize_loop()
    
    #with synth as Synthesizer():
        #synth.select_voice('Microsoft Server Speech Text to Speech Voice (en-US, ZiraPro)')
        #synth.speak('Sorry, I\'m not sure how to help with that.')
