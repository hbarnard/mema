import replicate
model = replicate.models.get("openai/whisper")
from pathlib import Path
audio_file = Path('/var/spool/mema/OSR_us_000_0010_8k.wav')
output = model.predict(audio=audio_file)

