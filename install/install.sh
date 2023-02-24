#!/usr/bin/env bash

# things to be added 21/1/2023
# npm install node-red-contrib-pythonshell
# python modules for face unlock
#
# 15/2/2023
# we're now assuming mema user now with root privileges via visudo?
# this may need some adjustment too, first user on pi is root
# 
# FIXME timesync doesn't work hence ntpspec/clock pi problems 'anyway'

echo  '*-------------------------------------------------------------------------------*'
echo 'this will try to install mema3, control-c to abort, sleeping for 10 seconds'
echo 'make sure that the system date on the Pi is correct otherwise certs are invalid'
echo  '*-------------------------------------------------------------------------------*'
sleep 10
echo  '*-------------------------------------------------------------------------------*'
echo 'system update and upgrade to start with'
echo  '*-------------------------------------------------------------------------------*'
apt update
apt upgrade

echo  '*-------------------------------------------------------------------------------*'
echo 'making media directories'
echo  '*-------------------------------------------------------------------------------*'

# -p just in case
mkdir -p static/media/mos
mkdir -p static/media/tmp
mkdir -p static/media/rec
mkdir -p static/media/vid
mkdir -p static/media/pic
mkdir -p var/log/mema
mkdir -p face_onboarding/dataset

echo  '*-------------------------------------------------------------------------------*'
echo 'installing packages'
echo  '*-------------------------------------------------------------------------------*'
apt install python3-pip
apt install python3-numpy
apt install python3-pycurl
apt install python3-pyaudio 
apt install python3-matplotlib python3-tk
apt install mosquitto mosquitto-dev
apt install sqlite3 
apt install ntpsec
apt install cmake

#FIXME: face sign in only, are these really necessary?
apt install libx11-dev
apt install libgtk-3-dev

# may or may not need ffmpeg for sample conversion
apt install ffmpeg
#FIXME: no portaudio package?
apt install portaudio19-dev 
#FIXME: fswebcam is only used on the laptop, libcamera on the pi
apt install fswebcam 
apt install curl
#FIXME: not part of the main software, but v. useful when testing
apt install sqlitebrowser

apt install chromium-browser
# FIXME: is this guile2.0 or 3.0 either will 'work'
apt install guile3.0
sudo apt install docker.io
echo  '*-------------------------------------------------------------------------------*'
echo 'installing mema3'
echo 'install python3 packages, make take a while'
echo  '*-------------------------------------------------------------------------------*'
sudo -H pip install -r  requirements/requirements.txt
echo  '*-------------------------------------------------------------------------------*'
echo 'installing intent server service'
cp etc/systemd/intent_server.service /etc/systemd/system/
systemctl enable intent_server
echo 'installing face unlock server service'
cp etc/systemd/unlock_server.service /etc/systemd/system/
systemctl enable unlock_server

#FIXME: need to copy based on system pi or laptop
printf 'Is this a pi (y/n)? '
old_stty_cfg=$(stty -g)
stty raw -echo ; answer=$(head -c 1) ; stty $old_stty_cfg # Careful playing with stty
if [ "$answer" != "${answer#[Yy]}" ];then
    cp etc/mema_pi.ini etc/mema.ini
    cp associations /home/mema/.config
    echo 'mema_pi.ini copied to mema.ini'
else
    cp etc/mema_laptop.ini etc/mema.ini
    cp associations /home/mema/.config
    echo 'assuming laptop, mema_laptop.ini copied to mema.ini'
fi

echo  '*-------------------------------------------------------------------------------*'
echo 'trying to start containers mema_rhasspy, mema_nodered, mema_mimic3'

#FIXME: pi should use mema user now?
usermod -aG docker mema
docker run -d --network host --name mema_rhasspy --restart unless-stopped -v "$HOME/.config/rhasspy/profiles:/profiles" -v "/etc/localtime:/etc/localtime:ro" --device /dev/snd:/dev/snd rhasspy/rhasspy --user-profiles /profiles --profile en
docker run --network host -d --restart unless-stopped --name mema_mimic3 -v "${HOME}/.local/share/mycroft/mimic3:/home/mimic3/.local/share/mycroft/mimic3" 'mycroftai/mimic3'
docker run -d --network host -v node_red_data:/data --restart unless-stopped --name mema_nodered nodered/node-red

#FIXME: Is this correct docker stuff runs as root?
echo 'copying rough rhasspy profile to /root/.config/rhasspy/profiles/en'
cp rhasspy/profiles/en/profile.json /root/.config/rhasspy/profiles/en
echo 'copying sentences.ini to /root/.config/rhasspy/profiles/en'
cp rhasspy/profiles/en/sentences.ini /root/.config/rhasspy/profiles/en

echo 'please reboot rhasspy and do manual configuration after this!'

#FIXME: The only thing in this should be the replicate API token
cp env /home/mema/.env

echo  '*-------------------------------------------------------------------------------*'
echo 'trying to start systemd servers'
systemctl daemon-reload
echo 'starting intent server'
systemctl start intent_server
echo 'starting face unlock server'
systemctl start unlock_server
echo  '*-------------------------------------------------------------------------------*'
echo 'almost done!'
echo 'trying to install the binary for jaro at https://github.com/isamert/jaro.git'
git clone https://github.com/isamert/jaro.git
cp jaro/jaro /usr/local/bin

echo 'rhasspy will (probably) need further manual set up at http://localhost:12101'
echo 'please reboot now'
exit 0
