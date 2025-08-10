# AIY Voice Kit Clock 🕰️

A voice clock with a one button interface.

## Prerequisites

## Getting Started

### Local dev environment

Hint: Define your AWS SSO profile with `export AWS_PROFILE=<profile-name>`.

### Customize the Raspberry Pi

Establish an SSH connection with the Raspberry Pi.

Install media player `mpg123` with:

```bash
sudo apt install mpg123
```

> [!NOTE]
> Adjust the volume level by calling `alsamixer` in the SSH console.

Start app at Raspberry Pi startup:

```bash
sudo mv ~/voicekit-clock.service /etc/systemd/system/
sudo chown root:root /etc/systemd/system/voicekit-clock.service
sudo systemctl enable voicekit-clock.service
sudo systemctl start voicekit-clock.service
```

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
