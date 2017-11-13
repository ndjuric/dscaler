#!/bin/bash
docker service create --mode global --mount type=volume,volume-opt=o=addr=10.135.69.119,volume-opt=device=:/nfs,volume-opt=type=nfs,target=/nfs --name nfstest alpine top