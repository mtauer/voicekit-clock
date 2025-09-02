# Setup Guide

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

Optional: Adjust volume:

```bash
alsamixer
```

Create the project directory:

```bash
cd AIY-projects-python/src/
mkdir voicekit-clock
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

What this deploys:

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

Sync the client app to the Pi:

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

Optional: Check client app health:

```bash
sudo systemctl status voicekit-clock.service
sudo journalctl -u voicekit-clock.service --since "5 minutes ago"
```

Reload/restart after changes:

```bash
sudo systemctl daemon-reload
sudo systemctl restart voicekit-clock.service
```
