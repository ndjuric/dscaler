#!/usr/bin/env python3

DOCTL = "/usr/local/bin/doctl"
PK_FILE = "/home/ndjuric/.ssh/id_rsa.pub"
SWARM_DIR = TAG = "swarm"
OVERLAY_NETWORK = "swarmnet"
DOCKER_REGISTRY = {
    'master': 'docker.insocl.com:5000/master',
    'worker': 'docker.insocl.com:5000/worker'
}

SCRIPT_CREATE = "#!/bin/bash\n"
SCRIPT_CREATE += "ufw allow 2377/tcp\n"
SCRIPT_CREATE += "export "
SCRIPT_CREATE += "PUBLIC_IPV4=$(curl -s http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address)\n"
SCRIPT_CREATE += "docker swarm init --advertise-addr \"${PUBLIC_IPV4}:2377\"\n"
SCRIPT_CREATE += "docker network create --driver overlay {0}\n".format(OVERLAY_NETWORK)
SCRIPT_CREATE += "docker service create --network {0} --name {1} {2}\n".format(
    'swarmnet',
    'master',
    DOCKER_REGISTRY['master']
)
SCRIPT_CREATE += "docker service create --network {0} --name {1} {2}\n".format(
    'swarmnet',
    'worker',
    DOCKER_REGISTRY['worker']
)

SCRIPT_JOIN = "#!/bin/bash\n"
SCRIPT_JOIN += "ufw allow 2377/tcp\n"
SCRIPT_JOIN += "export "
SCRIPT_JOIN += "PUBLIC_IPV4=$(curl -s http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address)\n"
SCRIPT_JOIN += "docker swarm join --advertise-addr \"${{PUBLIC_IPV4}}:2377\" --token \"{0}\" \"{1}:2377\"\n"
