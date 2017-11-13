#!/bin/bash
	doctl compute droplet create $1 -v $2 \
		--image docker-16-04 \
		--size c-4 \
		--tag-name $3 \
		--enable-private-networking \
		--region fra1 \
		--ssh-keys $4 \
		--user-data-file $5