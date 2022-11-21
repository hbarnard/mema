#!/usr/bin/env bash

#docker stop mema_rhasspy
#docker stop mema_nodered
#docker stop mycroftai/mimic3

#docker rm rhasspy
#docker rm mema_nodered
#docker rm mycroftai/mimic3

docker run -d --network host --name mema_rhasspy --restart unless-stopped -v "$HOME/.config/rhasspy/profiles:/profiles" -v "/etc/localtime:/etc/localtime:ro" --device /dev/snd:/dev/snd rhasspy/rhasspy --user-profiles /profiles --profile en

docker run -d  --name mema_mimic3 --restart unless-stopped --network host -v "${HOME}/.local/share/mycroft/mimic3:/home/mimic3/.local/share/mycroft/mimic3" mycroftai/mimic3

docker run -d --network host -v node_red_data:/data --restart unless-stopped --name mema_nodered nodered/node-red

