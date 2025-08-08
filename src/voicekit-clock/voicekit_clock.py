#!/usr/bin/env python3
import time

from aiy.board import Board, Led

from utils.audio import play_audio
from utils.multi_event_detector import MultiEventDetector


def button_press_callback(count: int, *, board: Board) -> None:
    if count == 1:
        time.sleep(0.4)  # simulate remote processing time
        play_audio("./assets/time_12_29.mp3", "Es ist jetzt 12 Uhr 29.")
    else:
        time.sleep(2)  # simulate remote processing time
        play_audio(
            "./assets/time_12_29_weather_forecast.mp3",
            "Guten Tag! Es ist jetzt 12:29 in Berlin.\n\nDer Himmel zeigt sich stark bewölkt, bei etwa 26 Grad Celsius. Im weiteren Tagesverlauf bleibt es durchgehend bewölkt, und die Temperaturen erreichen bis zum Nachmittag rund 27 Grad. Am Abend kühlt es auf etwa 22 Grad ab.",
        )

    # After the audio output, switch off the LED
    board.led.state = Led.OFF


def main():
    detector = MultiEventDetector(button_press_callback)
    with Board() as board:
        print("🕰️  VoiceKit Clock - Detecting button press events ...")
        play_audio("./assets/starting.mp3", "...starte Sprachuhr.")
        while True:
            if board.button.wait_for_press():
                # Switch LED on before the debounce time for the button events
                # has ended to give a more immediate feedback to the user.
                board.led.state = Led.ON

                detector.handle_event(None, board=board)
                # small debounce delay
                time.sleep(0.01)


if __name__ == "__main__":
    main()
