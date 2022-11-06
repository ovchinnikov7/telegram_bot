import os

from speechkit import Session, SpeechSynthesis


class Yandex:
    speed = 1.0
    voices = ['alyss', 'jane', 'oksana', 'omazh', 'zahar', 'ermil', 'alena', 'filipp']
    voice = voices[6]
    emotions = ['good', 'evil', 'neutral']
    emotion = emotions[0]
    languages = ['ru-RU', 'en-US']
    language = languages[0]

    def __init__(self):
        api_key = os.environ.get('YANDEX_API_KEY')
        folder_id = os.environ.get('YANDEX_FOLDER_ID')

        self.session = Session(auth_type=Session.API_KEY, credential=api_key, folder_id=None,
                               x_client_request_id_header=True)

    def tts(
            self,
            text: str,
            file_path: str = "./",
            voice: str = voice,
            language_code: str = language,
            emotion: str = emotion,
            speed: str = speed,
            audio_format: str = "oggopus",
    ) -> str:
        synthesizer = SpeechSynthesis(self.session)
        synthesizer.synthesize(
            file_path=file_path,
            language_code=language_code,
            text=text,
            voice=voice,
            emotion=emotion,
            speed=speed,
            format=audio_format,
        )
        return file_path

    def stt(self, message, bot) -> str:
        pass
