#!/usr/bin/python
import subprocess
import json
import time
import os


class Command(object):
    def __init__(self):
        pass

    def parse_json(self, result):
        if not self.is_json(''.join(result)):
            return {'status': False, 'message': 'Not a JSON object'}

        return json.loads(''.join(result))

    @staticmethod
    def is_json(text):
        try:
            json_object = json.loads(text)
        except ValueError:
            return False
        return True

    @staticmethod
    def run(command):
        command = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = command.stdout.readlines()
        if not result:
            return command.stderr.readlines()

        clean_result = []
        for line in result:
            clean_result.append(line.rstrip())

        return clean_result


class SSH(Command):
    def __init__(self):
        super(SSH, self).__init__()

    def execute(self, user, host, command):
        return self.run(["ssh -o \"StrictHostKeyChecking no\" %s@%s %s" % (user, host, command)])

    def get_local_fingerprint(self, path_to_public_key):
        ssh_keygen_cmd = 'ssh-keygen -E md5 -lf {0}'.format(path_to_public_key)
        ssh_key = self.run([ssh_keygen_cmd])
        ssh_key = ''.join(ssh_key)
        key = ssh_key.split(' ')[1][4:]
        return key


class Digitalocean(SSH):
    def __init__(self, doctl_path, public_key_file):
        super(Digitalocean, self).__init__()
        self.doctl = doctl_path
        self.filter_tag = False
        self.ssh_key = self.get_local_fingerprint(public_key_file)

        if not os.path.exists(SWARM_DIR):
            os.makedirs(SWARM_DIR)

    def set_filter_tag(self, tag):
        self.filter_tag = tag

    def ls(self):
        droplet_list = self.run('./scripts/list.sh')
        droplets = self.parse_json(droplet_list)
        filtered = []
        for droplet in droplets:
            if ('tags' in droplet) and self.filter_tag:
                if self.filter_tag in droplet['tags']:
                    filtered.append(droplet)
        if not filtered:
            return droplets

        return filtered

    def list_single_node(self):
        droplet_list = self.run('./scripts/list-single-node.sh')
        return ''.join(droplet_list)

    def create_tag(self):
        if self.filter_tag:
            return self.run('./scripts/create-tag.sh ' + str(self.filter_tag))
        return False

    @staticmethod
    def generate_swarm_join(swarm_key, droplet_ip):
        fh = open(SWARM_DIR + '/join.sh', 'w')
        fh.write(SCRIPT_JOIN.format(swarm_key, droplet_ip))
        fh.close()

    @staticmethod
    def generate_swarm_create():
        fh = open(SWARM_DIR + '/create.sh', 'w')
        fh.write(SCRIPT_CREATE)
        fh.close()

    def add_manager(self):
        self.create_tag()

        droplet_ip = self.list_single_node()
        new_droplet = TAG + '-' + str(time.time())
        if not droplet_ip:
            print "Creating a new swarm host: {0} (takes about a minute)".format(new_droplet)
            self.generate_swarm_create()
            self.run('./scripts/swarm-create.sh {0} {1} {2} {3}'.format(new_droplet, TAG, self.ssh_key, SWARM_DIR))
            return True

        result = self.execute('root', droplet_ip, 'docker swarm join-token -q manager')
        swarm_key = ''.join(result)

        self.generate_swarm_join(swarm_key, droplet_ip)

        self.run("chmod a+x {0}/*.sh".format(SWARM_DIR))
        print "Joining an existing swarm: {0}/{1} (takes about a minute)".format(new_droplet, droplet_ip)
        self.run('./scripts/swarm-join.sh {0} {1} {2} {3}'.format(new_droplet, TAG, self.ssh_key, SWARM_DIR))
        return True

    def add_worker(self):
        droplet_ip = self.list_single_node()

        if not droplet_ip:
            print "In order to add a worker node, a manager node must exist first"
            return False

        new_droplet = TAG + '-' + str(time.time())
        result = self.execute('root', droplet_ip, 'docker swarm join-token -q worker')
        swarm_key = ''.join(result)
        self.generate_swarm_join(swarm_key, droplet_ip)
        self.run("chmod a+x {0}/*.sh".format(SWARM_DIR))

        print "Joining an existing swarm: {0}/{1} (takes about a minute)".format(new_droplet, droplet_ip)
        print './scripts/swarm-join.sh {0} {1} {2} {3}'.format(new_droplet, TAG, self.ssh_key, SWARM_DIR)
        self.run('./scripts/swarm-join.sh {0} {1} {2} {3}'.format(new_droplet, TAG, self.ssh_key, SWARM_DIR))
        return True

    @staticmethod
    def get_public_ip(droplet):
        for network in droplet['networks']['v4']:
            if network['type'] == 'public':
                return network['ip_address']
        return False


# temporary
def list_droplets():
    doctl = Digitalocean(DOCTL, PK_FILE)
    doctl.set_filter_tag(TAG)
    droplets = doctl.ls()
    for droplet in droplets:
        droplet_ip = doctl.get_public_ip(droplet)
        print droplet_ip


def add_manager():
    doctl = Digitalocean(DOCTL, PK_FILE)
    doctl.set_filter_tag(TAG)
    doctl.add_manager()


def main():
    doctl = Digitalocean(DOCTL, PK_FILE)
    doctl.set_filter_tag(TAG)
    doctl.add_worker()
    # add worker


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
