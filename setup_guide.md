# Setup Guide

### 📦 Prepare AIY Voice Kit v1

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

Configure the root project .env, which the `task` commands read:

```bash
cp .env.example .env
# set AWS_PROFILE=<your-sso-profile> (a [profile ...] entry in ~/.aws/config)
```

Create & activate a virtual environment; install CDK/infra dependencies:

```bash
cd infra/cdk
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Log in to AWS:

```bash
task infra:login
```

Commands run directly rather than through `task` (`cdk bootstrap` and the `aws` commands below) don't read the .env. Export the profile in that shell first:

```bash
export AWS_PROFILE=<your-sso-profile>
```

If this is your first time with CDK in the target account/region:

```bash
cdk bootstrap
```

Enable the LLM (Claude Sonnet 4.6 in Amazon Bedrock, set in `BEDROCK_MODEL_ID` in the stack) once per AWS account, before the first deploy:

- If the account has never used an Anthropic model in Bedrock, submit Anthropic's first-time use form: in the Bedrock console for the `bedrock-runtime` endpoint (region `eu-central-1`; the newer `bedrock-mantle` console lists no Anthropic models there), open **Model catalog**, choose an Anthropic model and follow the prompt.
- Invoke the model once as an admin user, so that Bedrock creates the AWS Marketplace subscription for it (the Lambda role is not allowed to do this). Use the Bedrock playground, or:

  ```bash
  aws bedrock-runtime converse --region eu-central-1 --model-id eu.anthropic.claude-sonnet-4-6 --messages '[{"role":"user","content":[{"text":"Hallo"}]}]'
  ```

- Wait until the subscription is ready (this can take up to 15 minutes); the status must be `AVAILABLE`:

  ```bash
  aws bedrock get-foundation-model-availability --region eu-central-1 --model-id anthropic.claude-sonnet-4-6
  ```

- Only a successful call proves access. AWS releases new models to accounts gradually: a call can fail with "is not available for this account" even when every status above looks fine. In that case use an older active model, or ask AWS Support to release the model to the account.

Deploy the serverless backend:

```bash
task infra:deploy
```

What this deploys:

- Amazon API Gateway (voicekit-clock-api)
- AWS Lambda functions (serverless Python 3.12 handlers)
- IAM roles/policies for least-privilege access
- Integration points for AWS Polly (de-DE TTS)
- Inference access for Anthropic Claude Sonnet 4.6 LLM (Amazon Bedrock, EU cross-region profile)

You can inspect everything in `infra/cdk/stacks/voicekit_clock_stack.py`.

---

### 💾 Install the app on the Raspberry Pi

In the root project .env (created above), set the Pi's address:

```bash
# set PI_HOST=<the Pi IP, e.g., 192.168.?.?>
```

Configure the client app .env:

```bash
cp src/voicekit-clock/.env.example src/voicekit-clock/.env
# set API_BASE_URL (Find in AWS Console → API Gateway → voicekit-clock-api → Stages → Invoke URL)
# set API_KEY
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
