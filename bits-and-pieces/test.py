


import os

import pytest
import replicate
from pathlib import Path
import microphone
import threading


rec = microphone.MicRecorder('./audio-clips', overlap=2)
#rec.start_recording()


#model = replicate.models.get("openai/whisper")

#audio_file = Path('/var/spool/mema/OSR_us_000_0010_8k.wav')
#result = model.predict(audio=audio_file)
#transcription = result["text"].lower()
#print(result)
#output = model.predict(audio=audio_file)



'''
#@pytest.mark.parametrize('model_name', whisper.available_models())
def test_transcribe(model_name: str):
    model = whisper.load_model(model_name).cuda()
    audio_path = os.path.join(os.path.dirname(__file__), "jfk.flac")

    language = "en" if model_name.endswith(".en") else None
    
    assert result["language"] == "en"

    transcription = result["text"].lower()
#    assert "my fellow americans" in transcription
#    assert "your country" in transcription
#    assert "do for you" in transcription

curl -s -X POST \
  -d '{"version": "770db50964b436879e870139c9c1504d6326774d8acc92e6815c19b68367ec51", "input": {"path": "/var/spool/mema/OSR_us_000_0010_8k.wav"}}' \
  -H "Authorization: Token ad79292f164f7d5a0f91ac4e66a7de7dde18d8e8 " \
  -H 'Content-Type: application/json' \
  https://api.replicate.com/v1/predictions

export REPLICATE_API_TOKEN=ad79292f164f7d5a0f91ac4e66a7de7dde18d8e8
'''
