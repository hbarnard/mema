#!/usr/bin/env bash

docker stop rhasspy
docker stop mema_nodered
docker stop mycroftai/mimic3

docker rm rhasspy
docker rm mema_nodered
docker rm mycroftai/mimic3

docker run -d  --name rhasspy --restart unless-stopped -v "$HOME/.config/rhasspy/profiles:/profiles" -v "/etc/localtime:/etc/localtime:ro" --device /dev/snd:/dev/snd rhasspy/rhasspy --user-profiles /profiles --profile en

sudo docker run --privileged -d --restart unless-stopped -v "${HOME}/.local/share/mycroft/mimic3:/home/mimic3/.local/share/mycroft/mimic3" 'mycroftai/mimic3'

docker run -d  -v node_red_data:/data --restart unless-stopped --name mema_nodered nodered/node-red

