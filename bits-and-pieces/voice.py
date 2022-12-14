import threading
from array import array
from Queue import Queue, Full
import os
import pytest


import pyaudio
import replicate





CHUNK_SIZE = 1024
MIN_VOLUME = 500
# if the recording thread can't consume fast enough, the listener will start discarding
BUF_MAX_SIZE = CHUNK_SIZE * 10

model = replicate.models.get("openai/whisper")


def main():
    stopped = threading.Event()
    q = Queue(maxsize=int(round(BUF_MAX_SIZE / CHUNK_SIZE)))

    listen_t = threading.Thread(target=listen, args=(stopped, q))
    listen_t.start()
    record_t = threading.Thread(target=record, args=(stopped, q))
    record_t.start()

    try:
        while True:
            listen_t.join(0.1)
            record_t.join(0.1)
    except KeyboardInterrupt:
        stopped.set()

    listen_t.join()
    record_t.join()


def record(stopped, q):
    while True:
        if stopped.wait(timeout=0):
            break
        chunk = q.get()
        vol = max(chunk)
        if vol >= MIN_VOLUME:
            # TODO: write to file
            print "O",
        else:
            print "-",


def listen(stopped, q):
    stream = pyaudio.PyAudio().open(
        format=pyaudio.paInt16,
        channels=2,
        rate=44100,
        input=True,
        frames_per_buffer=1024,
    )

    while True:
        if stopped.wait(timeout=0):
            break
        try:
            q.put(array('h', stream.read(CHUNK_SIZE)))
        except Full:
            pass  # discard

def write_and_transcribe(q):
    



if __name__ == '__main__':
    main()
