#!/usr/bin/env python3
from aiy.board import Board, Led
from aiy.voice.tts import say
import time

from utils.multi_event_detector import MultiEventDetector


def button_press_callback(count: int, *, board: Board) -> None:
    if count == 1:
        say("Es ist jetzt 13 Uhr 14.", lang="de-DE")
    else:
        say("Multi-Click", lang="de-DE")
    board.led.state = Led.OFF


def main():
    detector = MultiEventDetector(button_press_callback)
    with Board() as board:
        print("🕰️  VoiceKit Clock - Detecting button presses ...")
        while True:
            if board.button.wait_for_press():
                board.led.state = Led.ON
                detector.handle_event(None, board=board)

                # small debounce delay
                time.sleep(0.05)


if __name__ == "__main__":
    main()
