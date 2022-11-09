import os
import random

from speechkit import Session, SpeechSynthesis, ShortAudioRecognition


class Yandex:
    voices = ['alyss', 'filipp', 'ermil', 'jane', 'madirus', 'omazh', 'zahar']
    emotions = [
        ['neutral', 'good'],
        [],
        ['neutral', 'good'],
        ['evil', 'neutral', 'good'],
        [],
        ['evil', 'neutral'],
        ['neutral', 'good'],
    ]
    voice_actors = dict(zip(voices, emotions))

    def __init__(self):
        self.api_key = os.environ.get('YANDEX_API_KEY')
        self.oauth_token = os.environ.get('YANDEX_OAUTH_TOKEN')
        self.folder_id = os.environ.get('YANDEX_FOLDER_ID')

        self.session = Session.from_yandex_passport_oauth_token(self.oauth_token, self.folder_id)

    def tts(
            self,
            text: str,
            file_path,
    ) -> str:
        voice, emotions = random.choice(list(self.voice_actors.items()))
        emotion = random.choice(emotions)
        speed = '1.0'

        synthesizer = SpeechSynthesis(self.session)
        synthesizer.synthesize(
            file_path=file_path,
            text=text,
            lang='ru-RU',
            voice=voice,
            emotion=emotion,
            speed=speed,
            format='oggopus',
        )
        return f'{file_path}'

    def stt(self, audio) -> str:
        recognizer = ShortAudioRecognition(self.session)
        text = recognizer.recognize(
            audio,
            format='oggopus',
            sampleRateHertz='48000'
        )
        return text
