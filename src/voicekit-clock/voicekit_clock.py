#!/usr/bin/env python3
import datetime
import socket
import subprocess
import time

from aiy.board import Board, Led
from aiy.voice.tts import say


from utils.actions import get_next_action
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
            "./assets/de-DE/shutdown.mp3",
            "...beende die Sprachuhr.",
        )
        subprocess.run(["sudo", "shutdown", "-h", "now"])

    # After the audio output has finished, switch off the LED
    board.led.state = Led.OFF


def _advanced_actions(count: int) -> None:
    if count == 1:
        current_time_sentence = "Es ist jetzt {:%H:%M}.".format(datetime.datetime.now())
        synthesize_text(current_time_sentence)
    elif count == 2 or count == 3 or count == 4:
        # For multi-press events of count 2-4, let the server decide for the action
        action = get_next_action()
        if action["action_type"] == "say":
            synthesize_text(action["text"])
    elif count == 5:
        play_audio(
            "./assets/de-DE/fallback_instructions.mp3",
            "So functioniert die Sprachuhr:\n\nDrücke den grünen Knopf einmal, um die aktuelle Uhrzeit zu hören. Drücke ihn zweimal, für die Uhrzeit und zusätzlich einen kurzen Wetterbericht. Drücke ihn fünfmal, um diese Anleitung erneut zu hören. Drücke ihn sechsmal, um eine Selbstdiagnose zu starten. Und schließlich, drücke ihn siebenmal, um die Sprachuhr herunterzufahren.",
        )


def _fallback_actions(count: int) -> None:
    if count == 1:
        current_time_sentence = "Es ist jetzt {:%H:%M}.".format(datetime.datetime.now())
        say(current_time_sentence, lang="de-DE")
    elif count == 5:
        play_audio(
            "./assets/de-DE/fallback_instructions_fallback.mp3",
            "So functioniert die Sprachuhr:\n\nDrücke den grünen Knopf einmal, um die aktuelle Uhrzeit zu hören. Drücke ihn fünfmal, um diese Anleitung erneut zu hören. Drücke ihn sechsmal, um eine Selbstdiagnose zu starten. Und schließlich, drücke ihn siebenmal, um die Sprachuhr herunterzufahren.",
        )


def _is_connected(timeout: float = 3.0) -> bool:
    """
    Returns True if there's an active internet connection, False otherwise.
    Attempts a TCP connection to a stable public IP (Google's DNS).
    """
    try:
        # Use a well-known, highly available IP and port (Google DNS over TCP)
        host = "8.8.8.8"
        port = 53
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return True
    except OSError:
        return False


def _is_server_up() -> bool:
    # TODO: implement
    return True


def main():
    detector = MultiEventDetector(button_press_callback, debounce_delay=0.5)
    with Board() as board:
        print("🕰️  VoiceKit Clock - Detecting button press events ...")
        play_audio("./assets/de-DE/starting.mp3", "...starte Sprachuhr.")
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
