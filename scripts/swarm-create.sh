#!/bin/bash
	doctl compute droplet create $1 -v --wait \
		--image docker-16-04 \
		--size 2gb \
		--tag-name $2 \
		--enable-private-networking \
		--region ams3 \
		--ssh-keys $3 \
		--user-data-file ./cloud-init/create.sh