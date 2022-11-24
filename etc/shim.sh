#!/usr/bin/env bash

sleep 5
curl -X POST "http://localhost:12101/api/restart" -H "accept: text/plain"
exit
