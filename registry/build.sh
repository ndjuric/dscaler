#!/bin/bash
cd /root/video-transcoder
git pull
docker build -f Dockerfile.worker -t worker .
docker tag worker docker.insocl.com:5000/worker
docker push docker.insocl.com:5000/worker

docker build -f Dockerfile.master -t master .
docker tag master docker.insocl.com:5000/master
docker push docker.insocl.com:5000/master

docker rmi $(docker images | grep "<none>" | awk "{print $3}")
