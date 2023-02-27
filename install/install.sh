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
mkdir -p /home/mema/mema/static/media/mos
mkdir -p /home/mema/mema/static/media/tmp
mkdir -p /home/mema/mema/static/media/rec
mkdir -p /home/mema/mema/static/media/vid
mkdir -p /home/mema/mema/static/media/pic
mkdir -p /home/mema/mema/var/log/mema
mkdir -p /home/mema/mema/face_onboarding/dataset
# keeps the k-means trained network
mkdir -p face_data

echo  '*-------------------------------------------------------------------------------*'
echo 'installing packages'
echo  '*-------------------------------------------------------------------------------*'
apt install -y python3-pip
apt install -y python3-numpy
apt install -y python3-pycurl
apt install -y python3-pyaudio 
apt install -y python3-matplotlib python3-tk
apt install -y mosquitto mosquitto-dev
apt install -y sqlite3 
apt install -y ntpsec
apt install -y cmake
apt install -y imagemagick

#FIXME: face sign in only, are these really necessary?
apt install -y libx11-dev
apt install -y libgtk-3-dev

# better to have this, especially with migration to ubuntu
apt install -y ffmpeg
#FIXME: no portaudio package?
apt install -y portaudio19-dev 
#FIXME: fswebcam is only used on the laptop, libcamera on the pi
apt install -y fswebcam 
apt install -y curl
#FIXME: not part of the main software, but v. useful when testing
apt install -y sqlitebrowser

apt install -y chromium-browser
# FIXME: is this guile2.0 or 3.0 either will 'work'
apt install -y guile-3.0
apt install -y docker.io
echo  '*-------------------------------------------------------------------------------*'
echo 'installing mema3'
echo '*-------------------------------------------------------------------------------*'
echo 'installing intent server service'
cp /home/mema/mema/etc/systemd/intent_server.service /etc/systemd/system/
systemctl enable intent_server
echo 'installing face unlock server service'
cp /home/mema/mema/etc/systemd/unlock_server.service /etc/systemd/system/
systemctl enable unlock_server

#FIXME: need to copy based on system pi or laptop
printf 'Is this a pi (y/n)? '
old_stty_cfg=$(stty -g)
stty raw -echo ; answer=$(head -c 1) ; stty $old_stty_cfg # Careful playing with stty
if [ "$answer" != "${answer#[Yy]}" ];then
    cp /home/mema/mema/etc/mema_pi.ini ../etc/mema.ini
    cp /home/mema/mema/etc/associations /home/mema/.config
    echo 'mema_pi.ini copied to mema.ini'
    echo 'install precompiled dblib'
    wget https://github.com/prepkg/dlib-raspberrypi/releases/latest/download/dlib_64.deb
    sudo dpkg -i ./dlib_64.deb
    #swapoff /swapfile
    #fallocate -l 2G /swapfile
    #mkswap /swapfile
    #swapon /swapfile    
else
    cp /home/mema/mema/etc/mema_laptop.ini ../etc/mema.ini
    cp /home/mema/mema/etc/associations /home/mema/.config
    sudo -H pip install dlib
    echo 'assuming laptop, mema_laptop.ini copied to mema.ini'
fi

echo 'install python3 packages, make take a while'
echo  '*-------------------------------------------------------------------------------*'
sudo -H pip install -r  /home/mema/mema/requirements/requirements.txt
echo 
echo  '*-------------------------------------------------------------------------------*'
echo 'trying to start containers mema_rhasspy, mema_nodered, mema_mimic3'

#FIXME: pi should use mema user now?
usermod -aG docker mema
docker run -d --network host --name mema_rhasspy --restart unless-stopped -v "$HOME/.config/rhasspy/profiles:/profiles" -v "/etc/localtime:/etc/localtime:ro" --device /dev/snd:/dev/snd rhasspy/rhasspy --user-profiles /profiles --profile en
docker run --network host -d --restart unless-stopped --name mema_mimic3 -v "${HOME}/.local/share/mycroft/mimic3:/home/mimic3/.local/share/mycroft/mimic3" 'mycroftai/mimic3'
docker run -d --network host -v node_red_data:/data --restart unless-stopped --name mema_nodered nodered/node-red


#FIXME: Is this correct docker stuff runs as root?
#FIXME: Don't do this, it makes rhasspy restart constantly, final config must be done by hand
#echo 'copying rough rhasspy profile to /root/.config/rhasspy/profiles/en'
cp /home/mema/mema/rhasspy/profiles/en/profile.json /root/.config/rhasspy/profiles/en

#FIXME: Leave this 'for the moment'
echo 'copying sentences.ini to /root/.config/rhasspy/profiles/en'
cp /home/mema/mema/rhasspy/profiles/en/sentences.ini /root/.config/rhasspy/profiles/en

echo 'please reboot rhasspy and do manual configuration after this!'

#FIXME: The only thing in this should be the replicate API token
cp /home/mema/mema/env /home/mema/.env

echo 'copying the shortcuts for face onboarding to the desktop'
cp /home/mema/mema/etc/face_onboarding.desktop /home/mema/Desktop
cp /home/mema/mema/etc/face_train.desktop /home/mema/Desktop
chmod a+x /home/mema/Desktop/*.desktop


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
