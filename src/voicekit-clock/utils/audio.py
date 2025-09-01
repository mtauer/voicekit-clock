import contextlib
import logging
import os
import subprocess
import urllib.parse
import urllib.request


def play_audio(mp3_path: str, content: str) -> None:
    """
    Convert and play synthesized speech audio on the Raspberry Pi.

    This function takes an MP3 file, converts it to a 48 kHz WAV file using
    `mpg123`, and then plays the WAV with `aplay`. The conversion step is
    necessary because direct playback of MP3s through ALSA on the AIY Voice
    Kit often results in crackling or distorted sound. WAV at 48 kHz is handled
    much more reliably by the hardware.

    Args:
        mp3_path: Path to the MP3 file to play.
        content: The original text that was synthesized (logged for traceability).

    Notes:
        - Logs a warning if playback or cleanup fails.
        - Temporary WAV files are always removed in a `finally` block.
    """
    logging.info(f'🔈  "{content}"')

    try:
        wav_path = "voicekit_clock_audio.wav"

        # Convert MP3 to WAV
        subprocess.run(
            ["mpg123", "-r", "48000", "-w", wav_path, "-q", mp3_path],
            check=True,
        )
        # Play WAV file
        subprocess.run(["aplay", "-q", wav_path], check=True)

    except subprocess.CalledProcessError as e:
        logging.error(f"Playback with mpg123 failed: {e}")
    finally:
        try:
            # Remove temp wav file
            subprocess.run(["rm", wav_path], check=True)
        except subprocess.CalledProcessError as e:
            logging.warning(f"Remove temp wav file failed: {e}")


def synthesize_text(content: str) -> None:
    """
    Generate and play back speech audio for the given text.

    The method requests an MP3 audio stream from the backend
    and plays it via `play_audio`.

    Args:
        content: The text to be synthesized.
    """
    logging.info(f'🔤 -> 💿  "{content}"')

    api_base = os.environ.get("API_BASE_URL", "").rstrip("/")
    if not api_base:
        raise RuntimeError("Missing environment variable: API_BASE_URL")

    api_key = os.environ.get("API_KEY", "")
    if not api_key:
        raise RuntimeError("Missing environment variable: API_KEY")

    url = api_base + "/audio?" + urllib.parse.urlencode({"text": content})
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "audio/mpeg",
            "x-api-key": api_key,
        },
    )

    # Perform synthesis request and validate response
    try:
        with contextlib.closing(urllib.request.urlopen(req, timeout=15)) as resp:
            ct = resp.info().get("Content-Type", "")
            # Some gateways return "audio/mpeg" or "audio/mpeg; charset=binary"
            if not ct.lower().startswith("audio/mpeg"):
                raise Exception(f"Unexpected Content-Type: {ct}")

            data = resp.read()
            if not data:
                raise Exception("Empty audio payload from API")

    except Exception as e:
        raise Exception(f"Synthesis request failed: {e}")

    # Write to a temp mp3 file and play it
    mp3_path = "voicekit_clock_audio.mp3"
    try:
        with open(mp3_path, "wb") as f:
            f.write(data)
        play_audio(mp3_path, content)
    finally:
        try:
            subprocess.run(["rm", mp3_path], check=True)
        except subprocess.CalledProcessError as e:
            logging.warning("Remove temp mp3 file failed: %s", e)
