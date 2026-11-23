"""Short-lived Windows speech sessions for the local desktop assistant."""
from collections import deque
from difflib import SequenceMatcher
import logging
from pathlib import Path
import re
import secrets
import threading
import time
from urllib.parse import urlsplit


def words(value):
    return ' '.join(re.findall(r"[\w']+", value.lower()))


def microphone_driver():
    import clr
    clr.AddReference(str(Path(__file__).with_name('Ledger.Audio.dll')))
    from Ledger.Audio import MicrophoneStream
    return MicrophoneStream


class WindowsSpeech:
    def __init__(self, audio_stream=None, output_stream=None, device_id=None):
        import clr
        clr.AddReference('System.Speech, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35')
        from System.Speech.Recognition import SpeechRecognitionEngine, DictationGrammar, RecognizeMode
        from System.Speech.Synthesis import SpeechSynthesizer
        self.lock = threading.Lock()
        self.events = deque(maxlen=48)
        self.capture = None
        self.level = 0
        self.spoken = ''
        self.tail_until = 0
        self.speaking = False
        self.prompt = None
        self.engine = self.synth = None
        self.closed = False
        recognizers = list(SpeechRecognitionEngine.InstalledRecognizers())
        english = next((r for r in recognizers if r.Culture.TwoLetterISOLanguageName == 'en'), None)
        if english is None:
            raise ValueError('Install English speech recognition in Windows language settings and reopen Voice.')
        try:
            self.engine = SpeechRecognitionEngine(english)
            self.engine.LoadGrammar(DictationGrammar())
            if device_id:
                from System.Speech.AudioFormat import SpeechAudioFormatInfo, AudioBitsPerSample, AudioChannel
                self.capture = microphone_driver()(device_id)
                format_info = SpeechAudioFormatInfo(16000, AudioBitsPerSample.Sixteen, AudioChannel.Mono)
                self.engine.SetInputToAudioStream(self.capture, format_info)
            elif audio_stream is None:
                self.engine.SetInputToDefaultAudioDevice()
            else:
                self.engine.SetInputToWaveStream(audio_stream)
            self.synth = SpeechSynthesizer()
            if output_stream is not None:
                self.synth.SetOutputToWaveStream(output_stream)
            else:
                self.synth.SetOutputToDefaultAudioDevice()
            self.engine.AudioLevelUpdated += self.audio_level
            self.engine.SpeechRecognized += self.recognized
            self.engine.SpeechHypothesized += self.partial
            self.engine.SpeechRecognitionRejected += self.rejected
            self.engine.RecognizeCompleted += self.completed
            self.synth.SpeakCompleted += self.finished
            self.engine.RecognizeAsync(RecognizeMode.Multiple)
        except Exception:
            self.close()
            raise

    def is_echo(self, phrase):
        if not self.spoken or not (self.speaking or time.monotonic() < self.tail_until):
            return False
        if phrase in self.spoken:
            return True
        blocks = SequenceMatcher(None, phrase.split(), self.spoken.split(), autojunk=False).get_matching_blocks()
        return sum(block.size for block in blocks) >= .72 * len(phrase.split())

    def audio_level(self, sender, event):
        with self.lock:
            self.level = max(self.level, int(event.AudioLevel))

    def recognized(self, sender, event):
        value = str(event.Result.Text).strip()
        with self.lock:
            if value and not self.closed and not self.is_echo(words(value)):
                self.events.append({'type':'question' if event.Result.Confidence >= .40 else 'unclear', 'text':value[:1500]})

    def partial(self, sender, event):
        value = words(str(event.Result.Text))
        with self.lock:
            if value and not self.speaking and not self.closed and not self.is_echo(value):
                update = {'type':'hearing','text':str(event.Result.Text)[:180]}
                if self.events and self.events[-1]['type'] == 'hearing':
                    self.events[-1] = update
                else:
                    self.events.append(update)
            if self.speaking and value and not self.is_echo(value) and (len(value.split()) >= 2 or value in ('stop','wait','pause')):
                if not self.events or self.events[-1]['type'] != 'interrupt':
                    self.events.append({'type':'interrupt'})

    def rejected(self, sender, event):
        with self.lock:
            if not self.closed and not self.speaking and time.monotonic() > self.tail_until:
                self.events.append({'type':'unclear'})

    def completed(self, sender, event):
        with self.lock:
            if not self.closed:
                self.events.append({'type':'ended'})

    def finished(self, sender, event):
        with self.lock:
            if event.Prompt == self.prompt and not self.closed:
                self.speaking = False
                self.tail_until = time.monotonic() + 1
                self.events.append({'type':'spoken' if not event.Error else 'audioError'})

    def stop_speaking(self):
        with self.lock:
            self.prompt = None
            self.speaking = False
            self.tail_until = time.monotonic() + 1
        self.synth.SpeakAsyncCancelAll()

    def say(self, phrase):
        self.stop_speaking()
        with self.lock:
            self.spoken = words(phrase)
            self.speaking = True
            self.prompt = self.synth.SpeakAsync(phrase)

    def take_level(self):
        with self.lock:
            level, self.level = self.level, 0
            return max(level, self.capture.TakeLevel()) if self.capture is not None else level

    def drain(self):
        with self.lock:
            events = list(self.events)
            self.events.clear()
            return events

    def close(self):
        self.closed = True
        if self.capture is not None:
            self.capture.Close()
        for obj, stop in [(self.engine, 'RecognizeAsyncCancel'), (self.synth, 'SpeakAsyncCancelAll')]:
            if obj is not None:
                try:
                    getattr(obj, stop)()
                except Exception:
                    pass
                finally:
                    obj.Dispose()


class VoiceBridge:
    def __init__(self, window, origin):
        self.window = window
        self.origin = origin
        self.lock = threading.RLock()
        self.session = None
        self.token = None
        self.last_poll = 0

    def allowed(self):
        page = urlsplit(self.window.get_current_url() or '')
        return (page.scheme+'://'+page.netloc == self.origin and page.path in ('','/','/index.html','/neighborops.html')
                and self.window.evaluate_js("document.visibilityState==='visible' && document.querySelector('#aiVoiceDialog')?.open === true"))

    def voice_devices(self):
        if not self.allowed():
            return []
        try:
            driver=microphone_driver()
            devices=[{'id':str(pair.Key),'name':str(pair.Value)} for pair in driver.Devices()]
            try:
                endpoint=str(driver.DefaultEndpoint()).lower()
                for device in devices:device['default']=device['id'].lower().endswith(endpoint)
            except Exception:
                pass
            return devices
        except Exception:
            logging.warning('Could not list microphone inputs.')
            return []

    def voice_start(self, device_id=''):
        if not self.allowed():
            return {'error':'Open Voice in the Ledger desktop window.'}
        with self.lock:
            self.close()
            try:
                self.session = WindowsSpeech(device_id=device_id) if device_id else WindowsSpeech()
            except ValueError as e:
                return {'error':str(e)}
            except Exception:
                logging.warning('Windows speech devices could not start.')
                return {'error':'Windows could not open speech. Check your microphone, speaker, and microphone access for desktop apps in Windows Settings.'}
            self.token = secrets.token_hex(16)
            self.last_poll = time.monotonic()
            threading.Thread(target=self.watch, args=(self.token,), daemon=True).start()
            return {'token':self.token}

    def watch(self, token):
        while True:
            time.sleep(2)
            with self.lock:
                if token != self.token:
                    return
                if time.monotonic() - self.last_poll > 8:
                    self.close()
                    return

    def voice_command(self, token, action, phrase=''):
        with self.lock:
            if not self.session or token != self.token:
                return {'error':'The voice session ended.'}
            if action == 'end':
                self.close()
            elif action == 'poll':
                self.last_poll = time.monotonic()
                return {'events':self.session.drain(), 'level':self.session.take_level()}
            elif action == 'speak' and isinstance(phrase,str) and 0 < len(phrase) <= 4000:
                self.session.say(phrase)
            elif action == 'interrupt':
                self.session.stop_speaking()
            else:
                return {'error':'Unknown voice control.'}
            return {}

    def close(self):
        with self.lock:
            session, self.session = self.session, None
            self.token = None
            if session:
                session.close()
