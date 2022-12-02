#!/usr/bin/env bash

echo 'this will try to install mema3, control-c to abort, sleeping for 10 seconds'
sleep 10
echo 'system upgrade to start with'
apt update
apt dist-upgrade
echo 'installing packages'
apt install python3-pip
sudo apt install python3-numpy
sudo apt install python3-matplotlib python3-tk
apt install mosquitto mosquitto-client
sudo apt install docker.io
echo 'installing mema3'
echo 'install python3 packages, make take a while'
sudo -H pip install -r  requirements.txt
echo 'installing intent server service and starting'
cp etc/systemd/intent_server.service /etc/systemd/system/
cp etc/mema_pi.ini etc/mema.ini
systemctl daemon-reload
systemctl start intent_server
echo 'installing docker and starting containers'
#curl -fsSL https://get.docker.com -o get-docker.sh
#sudo sh get-docker.sh
usermod -aG docker pi
docker run -d --network host --name mema_rhasspy --restart unless-stopped -v "$HOME/.config/rhasspy/profiles:/profiles" -v "/etc/localtime:/etc/localtime:ro" --device /dev/snd:/dev/snd rhasspy/rhasspy --user-profiles /profiles --profile en
sudo docker run --network host -d --restart unless-stopped --name mema_mimic3 -v "${HOME}/.local/share/mycroft/mimic3:/home/mimic3/.local/share/mycroft/mimic3" 'mycroftai/mimic3'
docker run -d --network host -v node_red_data:/data --restart unless-stopped --name mema_nodered nodered/node-red
echo 'almost done!'
echo 'please install the binary for handlr at https://github.com/chmln/handlr'
exit 0
