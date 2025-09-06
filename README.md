# AIY Voice Kit Clock 🕰️

A **talking clock** for people who prefer listening over reading.

Designed for **simplicity and accessibility**, it speaks the **current time** or a **compact weather update** in **natural German** at the press of a single button. This proof of concept runs on a Raspberry Pi, uses **AWS** for serverless backend logic and **WeatherAPI.com** for forecast data, and plays audio via `mpg123`/ALSA on the Pi.

## Purpose

The project was created for a person with limited vision. The goal: a device that works with **one button**, gives **clear spoken feedback**, and avoids the complexity of menus or screens.

## Features

- **One-button interface** with multi-press patterns (no screen required).
- High-quality **German Text-to-speech** via AWS Polly.
- **Weather briefings** (date, weekday, time, compact forecast).
- **Boot-time auto start** (systemd service).
- **Lean Raspberry Pi setup** (no extra Python packages on the Pi; uses `mpg123` for playback).

All speech output is **German**. To maximize voice quality, a **generative** AWS Polly voice is used.

Audio examples:

- [Current time](https://github.com/user-attachments/assets/aae78b8f-c7c9-47f6-bf53-5cbd8f988418)
- [Weather forecast](https://github.com/user-attachments/assets/02c7838c-8edc-48a1-b8c7-bb2b9b0cc1c8)

## Prerequisites

- **Google AIY Voice Kit** [v1](https://aiyprojects.withgoogle.com/voice-v1/)  
  Built and tested with the first version of the voice kit. Newer versions will likely work with small adjustments.
- **Raspberry Pi 3** + MicroSD card
- **Wi-Fi** (or LAN)
- **AWS account**
- [WeatherAPI.com](https://www.weatherapi.com/) API key (free tier works)
- Dev machine: **Python 3.12**, **AWS CLI**, [Task](https://taskfile.dev/)

> [!NOTE]
> Pi-side code is compatible with **Python 3.7.3** (depending on the AIY image). Server-side Lambdas target **Python 3.12**.

## Getting Started

[Setup Guide](setup_guide.md)

## Usage

Operate everything with the single button. Multi-press events trigger actions:

- 1× — 🕰️ **Current time**
- 2× — 🌤️ **Weather forecast** + date, weekday & time (may take up to 15s to respond)
- 5× — ℹ️ **Instructions**
- 6× — 🔧 **Self-diagnosis**
- 7× — ⏻ **Shutdown**

(3×/4× are reserved and not used at the moment.)

## License

The project is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0). See [LICENSE](LICENSE) file for details.
