#!/usr/bin/env bash

# things to be added 21/1/2023
# npm install node-red-contrib-pythonshell
# python modules for face unlock
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

mkdir static/media/mos
mkdir static/media/tmp
mkdir static/media/rec
mkdir static/media/vid
mkdir static/media/pic

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
# may or may not need ffmpeg for sample conversion
apt install ffmpeg 
apt install portaudio portaudio19-dev 
#FIXME: fswebcam is only used on the laptop, libcamera on the pi
apt install fswebcam 
apt install curl 
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
    cp associations /home/pi/.config
    echo 'mema_pi.ini copied to mema.ini'
else
    cp etc/mema_laptop.ini etc/mema.ini
    cp associations /home/hbarnard/.config
    echo 'assuming laptop, mema_laptop.ini copied to mema.ini'
fi

echo  '*-------------------------------------------------------------------------------*'
echo 'trying to start containers'
usermod -aG docker pi
docker run -d --network host --name mema_rhasspy --restart unless-stopped -v "$HOME/.config/rhasspy/profiles:/profiles" -v "/etc/localtime:/etc/localtime:ro" --device /dev/snd:/dev/snd rhasspy/rhasspy --user-profiles /profiles --profile en
docker run --network host -d --restart unless-stopped --name mema_mimic3 -v "${HOME}/.local/share/mycroft/mimic3:/home/mimic3/.local/share/mycroft/mimic3" 'mycroftai/mimic3'
docker run -d --network host -v node_red_data:/data --restart unless-stopped --name mema_nodered nodered/node-red

echo 'copying rough rhasspy profile to /root/.config/rhasspy/profiles/en'
cp rhasspy/profiles/en/profile.json /root/.config/rhasspy/profiles/en

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

echo 'rhasspy will need further set up at http://localhost:12101'
echo 'please reboot now'
exit 0
