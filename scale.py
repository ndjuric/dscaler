#!/usr/bin/python
import time
from controllers import *


# temporary
def build_infrastucture():
    doctl = Digitalocean(DOCTL, PK_FILE, 'makonda', SWARM_DIR)

    number_of_nodes = int(doctl.get_number_of_nodes('manager')) + int(doctl.get_number_of_nodes('worker'))
    if int(number_of_nodes) == 0:
        print('Swarm does not exist, creating a new one.')
        doctl.add_manager()
        return True
    # worker_status = doctl.add_worker()
    # if worker_status is False:
    #    doctl.add_manager()


def main():
    start_time = time.time()
    build_infrastucture()
    end_time = time.time()
    print('Time elapsed: {0}s'.format(end_time - start_time))


if __name__ == '__main__':
    DOCTL = "/usr/local/bin/doctl"
    PK_FILE = "/home/ndjuric/.ssh/id_rsa.pub"
    SWARM_DIR = TAG = "swarm"

    SCRIPT_CREATE = "#!/bin/bash\n"
    SCRIPT_CREATE += "ufw allow 2377/tcp\n"
    SCRIPT_CREATE += "export "
    SCRIPT_CREATE += "PUBLIC_IPV4=$(curl -s http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address)\n"
    SCRIPT_CREATE += "docker swarm init --advertise-addr \"${PUBLIC_IPV4}:2377\"\n"

    SCRIPT_JOIN = "#!/bin/bash\n"
    SCRIPT_JOIN += "ufw allow 2377/tcp\n"
    SCRIPT_JOIN += "export "
    SCRIPT_JOIN += "PUBLIC_IPV4=$(curl -s http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address)\n"
    SCRIPT_JOIN += "docker swarm join --advertise-addr \"${{PUBLIC_IPV4}}:2377\" --token \"{0}\" \"{1}:2377\"\n"

    main()
