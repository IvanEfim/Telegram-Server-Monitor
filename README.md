# Telegram Server Monitor

Monitoring service writen in Python3 to be hosted on your own server.

**Configure your linux server**

```sh
# Create a special user for the bot
sudo adduser telegram --gecos "" --disabled-password

# Install Python 3 and its package manager
sudo apt-get install python3 python3-pip

# Install Python Requests and PSUtil Library
sudo python3 -m pip install requests psutil --upgrade
```

**Download and install Telegram Server Monitor**

```sh
# Change to the created user
su telegram
cd ~

git clone https://github.com/IvanEfim/telegram-server-monitor.git
cd telegram-server-monitor
cp config.template.py config.py

```
