#!/bin/bash
doctl compute droplet list --tag-name swarm --format PublicIPv4 --no-header | head -n1
