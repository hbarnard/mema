#!/bin/sh
xset -dpms     # disable DPMS (Energy Star) features.
xset s off     # disable screen saver
xset s noblank # don't blank the video device
#matchbox-window-manager -use_titlebar no &
#unclutter &    # hide X mouse cursor unless mouse activated
#/usr/bin/chromium --display=:0 --kiosk --incognito --window-position=0,0 http://localhost:8000/memories.html
