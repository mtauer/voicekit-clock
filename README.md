# AIY Voice Kit Clock 🕰️

A voice clock (and more) with a one button interface.

TODO:

- project description
- German language
- audio examples
- clarify this is a hobby POC, not production-grade.

## Prerequisites

- **AIY Voice Kit, v1** Although the project was build and only tested with the first version of the Voice Kit there are good changes that the current version would work similarly.
- Raspberry Pi 3 and a MicroSD card
- WiFi (or LAN)
- AWS account
- (free) API key for weatherAPI.com
- on the dev machine: AWS CLI, Python

## Getting Started

### 📦 Prepare Voice Kit Box

Install the system image as described [here](https://aiyprojects.withgoogle.com/voice-v1/) (download the `.img.xy` file from https://github.com/google/aiyprojects-raspbian/releases; connect MicroSD card; Use [Etcher](https://etcher.balena.io/) to flash the image).

Assemble the Voice Kit box as described insert the SD card, and connect a monitor, keyboard and a mouse. Then connect the Pi to power.

After a reboot, as the Pi needs to set up the MicroSD volume, follow the onboarding instructions (set country/language/timezone; change password; select WiFi network; update OS; restart).

From the desktop, run "Test audio" and "Test WiFi" to verify the hardware is working correctly.

In the terminal run

```bash
ip addr show wlan0
```

and note down the `inet` address (which looks like `192.168.?.?`).

You can now disconnect the monitor, keyboard and mouse from the Voice Kit box.

### 💻 Prepare Raspberry Pi for Software Installation

On a dev machine that is in the same WiFi network as the Voice Kit, run:

```bash
ssh pi@192.168.?.?
```

to establish an SSH connection with the Raspberry Pi.

On the Raspberry Pi install the media player `mpg123` with:

```bash
sudo apt install mpg123
```

> [!NOTE]
> Adjust the volume level by calling `alsamixer` in the SSH console.

Create a project directory with:

```bash
cd AIY-projects-python/src/
mkdir voicekit-clock
```

> [!NOTE]
> To avoid typing your `pi` user password each time run in a dev machine terminal (not the SSH session):
>
> ```bash
> ssh-keygen -t ed25519 # not needed if an SSH-key already exists
> ssh-copy-id pi@192.168.?.?
> ```

### ☁️ Prepare Infrastructure

Duplicate the file `infra/cdk/.env.example` as `infra/cdk/.env` and fill in the [WeatherAPI](https://www.weatherapi.com/) key and weather location.

On MacOS and Linux, to manually create a virtual environment, activate it and install the required CDK/infra dependencies run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

To login to your AWS account run

```bash
task infra:login
```

> [!NOTE]
> If you are using an AWS SSO profile define it with `export AWS_PROFILE=<profile-name>`.

Only if this is your first time using CDK on your account, run the following. The command initializes resources needed for the AWS Cloud Development Kit (CDK).

```bash
cdk bootstrap
```

Finally, deploy server-side resources und functionality for the Voice Kit Clock run

```bash
task infra:deploy
```

In the file `infra/cdk/stacks/voicekit_clock_stack.py` you can find a detailed definition of all cloud services needed for the Voice Kit Clock.

### 💾 Install the app on the Raspberry Pi

Duplicate the file `.env.example` as `.env` and configure the `PI_HOST` IP.

Duplicate the file `src/voicekit-clock/.env.example` as `src/voicekit-clock/.env` and set the AWS API Gateway invoke URL as `API_BASE_URL` (AWS console -> API Gateway `voicekit-clock-api` -> Stages -> Invoke URL). Additionally set the API Gateway API key as `API_KEY`.

To copy the client-side part of the application to the Raspberry Pi, use:

```bash
task sync
```

Copy the service file to the Pi with:

```bash
task init
```

As a last step, log into the Raspberry Pi and and configure the app to start at Raspberry Pi startup

```bash
# establish SSH connect with: ssh pi@192.168.?.?
sudo mv ~/voicekit-clock.service /etc/systemd/system/
sudo chown root:root /etc/systemd/system/voicekit-clock.service
sudo systemctl enable voicekit-clock.service
sudo systemctl start voicekit-clock.service
```

After the service has started successfully, you should hear "...starte Sprachuhr".

Check the service with:

```bash
sudo systemctl status voicekit-clock.service
sudo journalctl -u voicekit-clock.service --since "5 minutes ago"
```

Restart the service with:

```bash
sudo systemctl daemon-reload
sudo systemctl restart voicekit-clock.service
```

## 🕰️ Usage

The Voice Kit clock is operated with a single button. Through multi-press evens multiple actions can be triggered.

Press the button:

- **1x** — **time**
- **2x** — **compact weather forecast plus date, weekday and time**
- 3x — not used
- 4x — not used
- 5x — instructions
- 6x — self-diagnosis
- 7x — shutdown
