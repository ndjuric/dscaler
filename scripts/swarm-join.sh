#!/bin/bash
	doctl compute droplet create $1 -v \
		--image docker-16-04 \
		--size 2gb \
		--tag-name $2 \
		--enable-private-networking \
		--region fra1 \
		--ssh-keys $3 \
		--user-data-file ./$4/join.sh