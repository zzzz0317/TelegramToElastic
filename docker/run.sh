#!/bin/sh
docker pull python:3-alpine
docker stop telegram-to-elastic
docker rm -f telegram-to-elastic
docker run -d --name telegram-to-elastic --restart="always" \
-v /srv/pods/telegram-to-elastic:/app \
--net=host \
python:3-alpine \
/app/start.sh
