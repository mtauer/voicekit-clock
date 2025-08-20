# AIY Voice Kit Clock 🕰️

A **talking clock** built for **simplicity and accessibility**. Press the green/red/white button on the Google **AIY Voice Kit** and hear the **current time** or a **compact weather update** — all spoken in **natural-sounding German**.  
This low-cost proof of concept runs on a Raspberry Pi, uses **AWS** for serverless backend logic and **WeatherAPI.com** for forecast data, and plays audio via `mpg123`/ALSA.

---

Example for the current time audio:

https://github.com/user-attachments/assets/aae78b8f-c7c9-47f6-bf53-5cbd8f988418

---

Example for the weather forecast audio:

https://github.com/user-attachments/assets/02c7838c-8edc-48a1-b8c7-bb2b9b0cc1c8

## Features

- **One-button interface** with multi-press actions (see Usage).
- **German TTS** via AWS Polly (de-DE voice).
- **Weather briefings** (date, weekday, time, compact forecast).
- **Boot-time auto start** (systemd service).
- **Lean Raspberry Pi setup** (no extra Python packages on the Pi; uses `mpg123` for playback).

> [!NOTE]
> All speech output is **German**. To maximize voice quality, a **generative** German Polly voice is configured.

## Prerequisites

- **Google AIY Voice Kit v1**  
  Built and tested with v1. Newer kits will likely work with small adjustments.
- **Raspberry Pi 3** + MicroSD card
- **Wi-Fi** (or LAN)
- **AWS account**
- [WeatherAPI.com](https://www.weatherapi.com/) API key (free tier works)
- Dev machine: **Python 3.12**, **AWS CLI**, [Task](https://taskfile.dev/)

> [!NOTE]
> Pi-side code is compatible with **Python 3.7.3** (AIY image). Server-side Lambdas target **Python 3.12**.

## Getting Started

### 📦 Prepare Voice Kit

**1) Flash the AIY image**

- Follow the official guide: <https://aiyprojects.withgoogle.com/voice-v1/>
- Download a release image: <https://github.com/google/aiyprojects-raspbian/releases>
- Flash the `.img.xz` to the MicroSD with [Etcher](https://etcher.balena.io/).

**2) First boot & hardware check**

- Assemble the Voice Kit, insert the SD card, connect monitor/keyboard/mouse, then power on.
- Complete onboarding: country/language/timezone, change password, select Wi-Fi, update OS, restart.
- From the desktop, run **“Test audio”** and **“Test Wi-Fi”**.
- In a terminal, find the Pi’s Wi-Fi IP:
  ```bash
  ip addr show wlan0
  ```
  Note the inet address (which looks like `192.168.?.?`).
- You can now disconnect monitor/keyboard/mouse for headless operation.

---

### 💻 Prepare Raspberry Pi for Software Installation

From your dev machine (same network as the Pi), SSH into the Pi:

```bash
ssh pi@192.168.?.?
```

Install the audio player:

```bash
sudo apt install mpg123
```

Adjust volume:

```bash
alsamixer
```

Create the project directory:

```bash
cd AIY-projects-python/src/
mkdir voicekit-clock
```

Optional: Set up passwordless SSH from your dev machine (not inside the SSH session):

```bash
ssh-keygen -t ed25519 # skip if you already have a key
ssh-copy-id pi@192.168.?.?
```

---

### ☁️ Prepare Infrastructure

Copy and fill the environment file:

```bash
cp infra/cdk/.env.example infra/cdk/.env
# set WEATHER_API_KEY and your weather location
```

Create & activate a virtual environment; install CDK/infra dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Log in to AWS:

```bash
# If using AWS SSO, run: export AWS_PROFILE=<your-sso-profile>
task infra:login
```

If this is your first time with CDK in the target account/region:

```bash
cdk bootstrap
```

Deploy the serverless backend:

```bash
task infra:deploy
```

What this deploys (at a glance):

- Amazon API Gateway (voicekit-clock-api)
- AWS Lambda functions (serverless Python 3.12 handlers)
- IAM roles/policies for least-privilege access
- Integration points for AWS Polly (de-DE TTS)
- Inference access for Anthropic Claude Sonnet 4 LLM

You can inspect everything in `infra/cdk/stacks/voicekit_clock_stack.py`.

In the AWS Console, activate model access for `Anthropic/Claude Sonnet 4` in Bedrock.

---

### 💾 Install the app on the Raspberry Pi

Configure the root project .env:

```bash
cp .env.example .env
# set PI_HOST=<the Pi IP, e.g., 192.168.?.?>
```

Configure the client app .env:

```bash
cp src/voicekit-clock/.env.example src/voicekit-clock/.env
# Set API_BASE_URL (In AWS Console → API Gateway → voicekit-clock-api → Stages → Invoke URL)
# Set API_KEY
```

Sync the client to the Pi:

```bash
task sync
```

Copy the systemd service file to the Pi:

```bash
task init
```

Enable auto-start and start client now (on the Pi):

```bash
# ssh pi@192.168.?.?  # if not already connected
sudo mv ~/voicekit-clock.service /etc/systemd/system/
sudo chown root:root /etc/systemd/system/voicekit-clock.service
sudo systemctl enable voicekit-clock.service
sudo systemctl start voicekit-clock.service
```

If successful, you should hear: “…starte Sprachuhr”.

Check service health:

```bash
sudo systemctl status voicekit-clock.service
sudo journalctl -u voicekit-clock.service --since "5 minutes ago"
```

Reload/restart after changes:

```bash
sudo systemctl daemon-reload
sudo systemctl restart voicekit-clock.service
```

## 🕰️ Usage

Operate everything with the single button. Multi-press events trigger actions:

- 1× — 🕰️ current time
- 2× — 🌤️ compact weather forecast plus date, weekday and time
- 5× — ℹ️ instructions
- 6× — 🔧 self-diagnosis
- 7× — ⏻ shutdown

(3×/4× are reserved and not used at the moment.)
