#!/usr/bin/env python3
from aiy.board import Board, Led
from aiy.voice.tts import say
import time

GERMAN_SENTENCE = "Es ist jetzt 18 Uhr 54."


def main():
    with Board() as board:
        while True:
            if board.button.wait_for_press():
                board.led.state = Led.ON
                say(GERMAN_SENTENCE, lang="de-DE")
                board.led.state = Led.OFF
                # small debounce delay
                time.sleep(0.2)


if __name__ == "__main__":
    main()
