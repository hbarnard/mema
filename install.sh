#!/usr/bin/env bash
echo  '*-------------------------------------------------------------------------------*'
echo 'this will try to install mema3, control-c to abort, sleeping for 10 seconds'
echo 'make sure that the system date on the Pi is correct otherwise certs are invalid'
echo  '*-------------------------------------------------------------------------------*'
sleep 10
echo  '*-------------------------------------------------------------------------------*'
echo 'system upgrade to start with'
echo  '*-------------------------------------------------------------------------------*'
apt update
apt dist-upgrade

echo  '*-------------------------------------------------------------------------------*'
echo 'making media directories'
echo  '*-------------------------------------------------------------------------------*'

mkdir -p static/media/mos
mkdir -p static/media/tmp
mkdir -p static/media/rec
mkdir -p static/media/vid
mkdir -p static/media/pic

echo  '*-------------------------------------------------------------------------------*'
echo 'installing packages'
echo  '*-------------------------------------------------------------------------------*'
# may not need some of these
apt install python3-pip
apt install python3-numpy
apt install python3-pycurl
apt install python3-matplotlib python3-tk
apt install mosquitto mosquitto-dev
apt install sqlite3
apt install cmake
# makes life simpler for debugging, not in core
apt install ack
# this is to enable the xdg-open replacement jaro
apt-get install guile-2.2
# audiovisual section
apt install ffmpeg
apt install libcamera-apps
apt install pulseaudio
apt install vlc
# docker
sudo apt install docker.io
echo  '*-------------------------------------------------------------------------------*'
echo 'installing mema3'
echo 'install python3 packages, make take a while'
echo  '*-------------------------------------------------------------------------------*'
sudo -H pip install -r  requirements.txt
#FIXME: voice bonnet stuff: not happy about this, does tons of 'other stuff' as well!
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo python3 raspi-blinka.py
echo  '*-------------------------------------------------------------------------------*'
echo 'installing intent server service'
cp etc/systemd/intent_server.service /etc/systemd/system/
cp etc/mema_pi.ini etc/mema.ini
systemctl daemon-reload
echo  '*-------------------------------------------------------------------------------*'
echo 'trying to start containers'
usermod -aG docker pi
docker run -d --network host --name mema_rhasspy --restart unless-stopped -v "$HOME/.config/rhasspy/profiles:/profiles" -v "/etc/localtime:/etc/localtime:ro" --device /dev/snd:/dev/snd rhasspy/rhasspy --user-profiles /profiles --profile en
sudo docker run --network host -d --restart unless-stopped --name mema_mimic3 -v "${HOME}/.local/share/mycroft/mimic3:/home/mimic3/.local/share/mycroft/mimic3" 'mycroftai/mimic3'
docker run -d --network host -v node_red_data:/data --restart unless-stopped --name mema_nodered nodered/node-red
echo  '*-------------------------------------------------------------------------------*'
echo 'starting intent server'
systemctl start intent_server
echo  '*-------------------------------------------------------------------------------*'
echo 'almost done!'
echo 'please install the binary for handlr at https://github.com/chmln/handlr'
exit 0
