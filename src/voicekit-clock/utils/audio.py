import subprocess


def play_audio(mp3_path: str, content: str) -> None:
    try:
        print(f'🔈  "{content}"')

        # Workaround explanation:
        # On the Raspberry Pi (especially with the AIY Voice Kit), playing MP3s directly with mpg123
        # sometimes causes crackling or sizzling noises due to mismatches between the MP3 audio format
        # and the ALSA audio output.
        #
        # By first converting the MP3 to a 48 kHz WAV file (a format ALSA handles more consistently),
        # and then playing it with `aplay`, we achieve clean and stable audio output without distortion.

        # Convert MP3 to WAV
        subprocess.run(
            ["mpg123", "-r", "48000", "-w", "temp.wav", "-q", mp3_path], check=True
        )
        # Play WAV file
        subprocess.run(["aplay", "-q", "temp.wav"], check=True)

    except subprocess.CalledProcessError as e:
        print(f"Playback with mpg123 failed: {e}")
