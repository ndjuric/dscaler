#!/usr/bin/env python3

DOCTL = "/usr/local/bin/doctl"
PK_FILE = "/home/ndjuric/.ssh/id_rsa.pub"
SWARM_DIR = TAG = "swarm"
OVERLAY_NETWORK = "swarmnet"
DOCKER_REGISTRY = {
    'master': 'private.docker.registry.example.com:5000/master',
    'worker': 'private.docker.registry.example.com:5000/worker'
}
NFS_SERVER = '10.135.69.119'

''' CALL_MAP is a list enumerating methods from the Cloud class the are allowed to be directly executed. '''
CALL_MAP = [
    'build',
    'deploy',
    'destroy',
    'add_worker',
    'add_manager',
    'ssh_manager',
    'logs_master',
    'remove_worker',
    'remove_manager',
    'get_master_container_id'
]

SCRIPT_CREATE = "#!/bin/bash\n"
SCRIPT_CREATE += "apt-get install -y nfs-common\n"
SCRIPT_CREATE += "mkdir /nfs\n"
SCRIPT_CREATE += "mount {0}:/nfs /nfs\n".format(NFS_SERVER)
SCRIPT_CREATE += "ufw allow 2377/tcp\n"
SCRIPT_CREATE += "export "
SCRIPT_CREATE += "PUBLIC_IPV4=$(curl -s http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address)\n"
SCRIPT_CREATE += "docker swarm init --advertise-addr \"${PUBLIC_IPV4}:2377\"\n"
SCRIPT_CREATE += "docker network create --driver overlay {0}\n".format(OVERLAY_NETWORK)

SCRIPT_CREATE += "docker service create "
SCRIPT_CREATE += "--network swarmnet "
SCRIPT_CREATE += "--name master "
SCRIPT_CREATE += "--mount type=bind,source=/nfs,target=/nfs {0} \n".format(DOCKER_REGISTRY['master'])

SCRIPT_CREATE += "docker service create --network swarmnet --name worker {0}\n".format(DOCKER_REGISTRY['worker'])
SCRIPT_CREATE += "docker service scale worker=5\n"

SCRIPT_JOIN = "#!/bin/bash\n"
SCRIPT_JOIN += "apt-get install -y nfs-common\n"
SCRIPT_JOIN += "mkdir /nfs\n"
SCRIPT_JOIN += "mount {0}:/nfs /nfs\n".format(NFS_SERVER)
SCRIPT_JOIN += "ufw allow 2377/tcp\n"
SCRIPT_JOIN += "export "
SCRIPT_JOIN += "PUBLIC_IPV4=$(curl -s http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address)\n"
SCRIPT_JOIN += "docker swarm join --advertise-addr \"${{PUBLIC_IPV4}}:2377\" --token \"{0}\" \"{1}:2377\"\n"
