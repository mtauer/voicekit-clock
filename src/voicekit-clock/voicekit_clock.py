#!/usr/bin/env python3
import datetime
import time
import sys

from aiy.board import Board, Led

from utils.audio import play_audio, synthesize_text
from utils.load_dotenv import load_dotenv
from utils.multi_event_detector import MultiEventDetector

load_dotenv()


def button_press_callback(count: int, *, board: Board) -> None:
    if count == 1:
        current_time_sentence = "Es ist jetzt {:%H:%M}.".format(datetime.datetime.now())
        synthesize_text(current_time_sentence)
    else:
        time.sleep(2)  # simulate remote processing time
        play_audio(
            "./assets/time_13_33_weather_forecast.mp3",
            "Guten Tag! Es ist jetzt 13:33 in Berlin.\n\nAktuell ist es überwiegend sonnig bei etwa 27 Grad Celsius. Am Nachmittag steigen die Temperaturen weiter bis auf rund 30 Grad. Auch am frühen Abend bleibt es weiterhin sonnig und angenehm - ein perfekter Spätsommertag!",
        )

    # After the audio output has finished, switch off the LED
    board.led.state = Led.OFF


def main():
    detector = MultiEventDetector(button_press_callback, debounce_delay=0.5)
    with Board() as board:
        print("🕰️  VoiceKit Clock - Detecting button press events ...")
        play_audio("./assets/starting.mp3", "...starte Sprachuhr.")
        while True:
            if board.button.wait_for_press():
                # Switch the LED on before the debounce time for the button events
                # has ended to give a more immediate feedback to the user.
                board.led.state = Led.ON

                detector.handle_event(None, board=board)
                # small debounce delay
                time.sleep(0.01)


if __name__ == "__main__":
    main()
