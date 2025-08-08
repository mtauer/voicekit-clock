import subprocess


def play_audio(file_path: str, content: str) -> None:
    try:
        print(f'🔈  "{content}"')
        subprocess.run(["mpg123", "-q", file_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Playback with mpg123 failed: {e}")
