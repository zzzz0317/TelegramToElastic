#!/bin/sh
docker pull python:3-alpine
docker run -it \
-v /srv/pods/telegram-to-elastic:/app \
--net=host \
python:3-alpine \
/app/gclist_in.sh
