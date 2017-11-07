#!/bin/bash
doctl compute droplet list --tag-name $1 --format Name,PublicIPv4 --no-header
