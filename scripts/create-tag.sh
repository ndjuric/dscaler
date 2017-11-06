#!/bin/bash

if [ "$1" != "" ]; then
    doctl compute tag create $1
else
    echo "Enter tag name."
fi