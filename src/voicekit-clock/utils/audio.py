import os
import subprocess
import urllib.request
import urllib.parse
import contextlib


def play_audio(mp3_path: str, content: str) -> None:
    print(f'🔈  "{content}"')
    try:
        # Workaround explanation:
        # On the Raspberry Pi (especially with the AIY Voice Kit), playing MP3s directly with mpg123
        # sometimes causes crackling or sizzling noises due to mismatches between the MP3 audio format
        # and the ALSA audio output.
        #
        # By first converting the MP3 to a 48 kHz WAV file (a format ALSA handles more consistently),
        # and then playing it with `aplay`, we achieve clean and stable audio output without distortion.

        wav_path = "voicekit_clock_audio.wav"

        # Convert MP3 to WAV
        subprocess.run(
            ["mpg123", "-r", "48000", "-w", wav_path, "-q", mp3_path],
            check=True,
        )
        # Play WAV file
        subprocess.run(["aplay", "-q", wav_path], check=True)

    except subprocess.CalledProcessError as e:
        print(f"Playback with mpg123 failed: {e}")


def synthesize_text(content: str) -> None:
    print(f'🔤 -> 💿  "{content}"')

    api_base = os.environ.get("API_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("API_KEY", "")

    if not api_base:
        raise RuntimeError("Missing environment variable: API_BASE_URL")
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

    # Perform request and validate Content-Type
    try:
        with contextlib.closing(urllib.request.urlopen(req, timeout=10)) as resp:
            ct = resp.info().get("Content-Type", "")
            # Some gateways return "audio/mpeg" or "audio/mpeg; charset=binary"
            if not ct.lower().startswith("audio/mpeg"):
                raise RuntimeError("Unexpected Content-Type: %s" % ct)

            data = resp.read()
            if not data:
                raise RuntimeError("Empty audio payload from API")

    except urllib.request.HTTPError as e:
        # Bubble up with more context
        raise RuntimeError("API HTTPError %s: %s" % (e.code, e.read()))
    except urllib.request.URLError as e:
        raise RuntimeError("API URLError: %s" % getattr(e, "reason", e))

    # Write to a temp file
    mp3_path = "voicekit_clock_audio.mp3"
    with open(mp3_path, "wb") as f:
        f.write(data)

    play_audio(mp3_path, content)
