#!/usr/bin/env python3
import datetime
import subprocess
import time

from aiy.board import Board, Led
from aiy.voice.tts import say


from utils.audio import play_audio, synthesize_text
from utils.load_dotenv import load_dotenv
from utils.multi_event_detector import MultiEventDetector

load_dotenv()


def button_press_callback(count: int, *, board: Board) -> None:
    if count <= 5:
        if not _is_connected() or not _is_server_up():
            _fallback_actions(count)
        else:
            _advanced_actions(count)

    elif count == 6:
        # TODO: Self-diagnosis
        pass
    else:
        # Shutdown
        play_audio(
            "./assets/shutdown.mp3",
            "...beende die Sprachuhr.",
        )
        subprocess.run(["sudo", "shutdown", "-h", "now"])

    # After the audio output has finished, switch off the LED
    board.led.state = Led.OFF


def _advanced_actions(count: int) -> None:
    if count == 1:
        current_time_sentence = "Es ist jetzt {:%H:%M}.".format(datetime.datetime.now())
        synthesize_text(current_time_sentence)
    elif count == 2:
        time.sleep(2)  # simulate remote processing time
        play_audio(
            "./assets/time_13_33_weather_forecast.mp3",
            "Guten Tag! Es ist jetzt 13:33 in Berlin.\n\nAktuell ist es überwiegend sonnig bei etwa 27 Grad Celsius. Am Nachmittag steigen die Temperaturen weiter bis auf rund 30 Grad. Auch am frühen Abend bleibt es weiterhin sonnig und angenehm - ein perfekter Spätsommertag!",
        )
    elif count == 5:
        play_audio(
            "./assets/fallback_instructions.mp3",
            "So functioniert die Sprachuhr:\n\nDrücke den grünen Knopf einmal, um die aktuelle Uhrzeit zu hören. Drücke ihn zweimal, für die Uhrzeit und zusätzlich einen kurzen Wetterbericht. Drücke ihn fünfmal, um diese Anleitung erneut zu hören. Drücke ihn sechsmal, um eine Selbstdiagnose zu starten. Und schließlich, drücke ihn siebenmal, um die Sprachuhr herunterzufahren.",
        )


def _fallback_actions(count: int) -> None:
    if count == 1:
        current_time_sentence = "Es ist jetzt {:%H:%M}.".format(datetime.datetime.now())
        say(current_time_sentence, lang="de-DE")
    elif count == 5:
        play_audio(
            "./assets/fallback_instructions_fallback.mp3",
            "So functioniert die Sprachuhr:\n\nDrücke den grünen Knopf einmal, um die aktuelle Uhrzeit zu hören. Drücke ihn fünfmal, um diese Anleitung erneut zu hören. Drücke ihn sechsmal, um eine Selbstdiagnose zu starten. Und schließlich, drücke ihn siebenmal, um die Sprachuhr herunterzufahren.",
        )


def _is_connected() -> bool:
    # TODO: implement
    return True


def _is_server_up() -> bool:
    # TODO: implement
    return True


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
