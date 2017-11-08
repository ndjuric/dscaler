#!/usr/bin/python
import subprocess
import time
import os


class Command(object):
    def __init__(self):
        pass

    @staticmethod
    def local_exec(command):
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

    def remote_exec(self, user, host, command):
        return self.local_exec(["ssh -o \"StrictHostKeyChecking no\" %s@%s %s" % (user, host, command)])

    def get_local_fingerprint(self, path_to_public_key):
        ssh_keygen_cmd = 'ssh-keygen -E md5 -lf {0}'.format(path_to_public_key)
        ssh_key = self.local_exec([ssh_keygen_cmd])
        ssh_key = ''.join(ssh_key)
        key = ssh_key.split(' ')[1][4:]
        return key


class Digitalocean(SSH):
    """ Digitalocean infrastructure management class """

    def __init__(self, doctl_path, public_key_file):
        super(Digitalocean, self).__init__()
        self.doctl = doctl_path
        self.filter_tag = TAG
        self.tags = self.set_node_tags()
        self.allowed_node_types = ['manager', 'worker']
        self.ssh_key = self.get_local_fingerprint(public_key_file)

        if not os.path.exists(SWARM_DIR):
            os.makedirs(SWARM_DIR)

    ''' Set the main tag (identifier) of the swarm, ie. name of the company, or name of the project '''

    def set_filter_tag(self, tag):
        self.filter_tag = tag
        self.set_node_tags()

    ''' Set swarm manager and worker tags, suffixes to the main tag of the swarm '''

    def set_node_tags(self):
        self.tags = {
            'manager': self.filter_tag + '-manager',
            'worker': self.filter_tag + '-worker'
        }
        return self.tags

    ''' List members of the swarm of type node_type (either manager or worker) '''

    def swarm_list(self, node_type):
        result = self.local_exec('./scripts/swarm-list.sh {0}'.format(self.tags[node_type]))
        if not result:
            return []

        swarm = []
        for node in result:
            node_info = node.split()
            swarm.append({
                'name': node_info[0],
                'ip': node_info[1]
            })

        return swarm

    ''' This one is pretty much straightforward. Destroys the swarm. '''

    def swarm_destroy(self):
        print 'Destroying swarm {0}'.format(self.filter_tag)
        swarm = []
        workers = self.swarm_list('worker')
        managers = self.swarm_list('manager')

        if workers:
            swarm += workers

        if managers:
            swarm += managers

        for host in swarm:
            self.purge_droplet(host['name'])

    ''' Get a single node of type node_type (either manager or worker) '''

    def get_node(self, node_type):
        result = self.local_exec('./scripts/swarm-list.sh {0} | head -n1'.format(self.tags[node_type]))
        if not result:
            return False
        node_info = result[0].split()
        node = {
            'name': node_info[0],
            'ip': node_info[1]
        }
        return node

    ''' Get number of nodes in the entire swarm for the set tag. '''

    def get_number_of_nodes(self, node_type):
        result = self.local_exec('./scripts/swarm-list.sh {0} | wc -l'.format(self.tags[node_type]))
        return ''.join(result)

    ''' Remove a worker node from the swarm and destroy its droplet. '''

    def remove_worker(self):
        node_type = 'worker'
        worker_info = self.get_node(node_type)
        if not worker_info:
            print "Worker removal failed, there are no workers tagged \"{0}\"".format(self.tags[node_type])
            return False

        print "Leaving the swarm..."
        self.drain_containers(worker_info['ip'], worker_info['name'])
        time.sleep(2)
        self.remote_exec(
            'root', worker_info['ip'], 'docker node rm {0} -f'.format(worker_info['name'])
        )
        self.purge_droplet(worker_info['name'])

    ''' Remove the swarm's manager node and destroy its droplet. '''

    def remove_manager(self):
        node_type = 'manager'
        number_of_managers = self.get_number_of_nodes()

        if int(number_of_managers) < 2:
            print "You need at least 2 managers in order to remove 1 manager."
            return False

        manager_info = self.get_node(node_type)
        if not manager_info:
            print "Node removal failed, there are no nodes tagged \"{0}\"".format(self.tags[node_type])
            return False

        print "Leaving the swarm..."
        self.drain_containers(manager_info['ip'], manager_info['name'])
        time.sleep(2)
        self.demote_manager(manager_info['ip'], manager_info['name'])
        self.purge_droplet(manager_info['name'])

    ''' Drain docker containers from a specified droplet IP. '''

    def drain_containers(self, ip, name):
        print 'Drainining containers from {0}@{1}...'.format(name, ip)
        self.remote_exec('root', ip, 'docker node update --availability drain {0}'.format(name))

    ''' Demote a swarm manager to worker, on a specified droplet IP. '''

    def demote_manager(self, ip, name):
        print 'Demoting {0}@{1} to worker...'.format(name, ip)
        self.remote_exec('root', ip, 'docker node demote {0}'.format(name))

    ''' Purge/destroy a digitalocean droplet. '''

    def purge_droplet(self, droplet_name):
        print "Purging droplet {0}...".format(droplet_name)
        return self.local_exec('./scripts/droplet-purge.sh {0}'.format(droplet_name))

    ''' Create a digitalocean tag, specified by node_type. '''

    def create_tag(self, node_type='worker'):
        if node_type not in self.allowed_node_types:
            print "Node type not allowed. Must be either 'manager' or 'worker'."
            return False

        if self.filter_tag:
            return self.local_exec('./scripts/create-tag.sh {0}'.format(str(self.tags[node_type])))

        return False

    ''' Generate a swarm join script and write it to a file. '''

    @staticmethod
    def generate_swarm_join(swarm_key, droplet_ip):
        fh = open(SWARM_DIR + '/join.sh', 'w')
        fh.write(SCRIPT_JOIN.format(swarm_key, droplet_ip))
        fh.close()

    ''' Generate a swarm create script and write it to a file. '''

    @staticmethod
    def generate_swarm_create():
        fh = open(SWARM_DIR + '/create.sh', 'w')
        fh.write(SCRIPT_CREATE)
        fh.close()

    ''' Swarm join functionality, this needs to be refactored'''

    def swarm_join(self, droplet_info, node_type='worker'):
        if node_type not in self.allowed_node_types:
            print "Node type not allowed. Must be either 'manager' or 'worker'."
            return False

        result = self.remote_exec('root', droplet_info['ip'], 'docker swarm join-token -q {0}'.format(node_type))
        swarm_key = ''.join(result)

        self.generate_swarm_join(swarm_key, droplet_info['ip'])
        self.local_exec("chmod a+x {0}/*.sh".format(SWARM_DIR))

        print "Joining an existing swarm: {0}@{1} (takes about a minute)".format(
            droplet_info['name'],
            droplet_info['ip']
        )

        droplet_name = "{0}-{1}".format(self.tags[node_type], str(time.time()))
        self.local_exec(
            './scripts/swarm-join.sh {0} {1} {2} {3}'.format(
                droplet_name,
                self.tags[node_type],
                self.ssh_key,
                SWARM_DIR
            )
        )
        return True

    ''' Use provided tag to lookup swarm status. If there's no swarm bring up a VM and set it up as a swarm manager. '''

    def add_manager(self):
        node_type = "manager"
        droplet_info = self.get_node(node_type)

        if droplet_info is not False:
            self.swarm_join(droplet_info, node_type)
            return True

        self.create_tag(node_type)
        droplet_name = "{0}-{1}".format(self.tags[node_type], str(time.time()))
        print "Creating a new swarm host: {0} (takes about a minute)".format(droplet_name)
        self.generate_swarm_create()

        self.local_exec(
            './scripts/swarm-create.sh {0} {1} {2} {3}'.format(
                droplet_name,
                self.tags[node_type],
                self.ssh_key,
                SWARM_DIR
            )
        )
        return True

    ''' Add a worker VM to Digitalocean. Use provided tag to join a swarm, if swarm manager VM exists. '''

    def add_worker(self):
        swarm_manager = self.get_node('manager')

        if swarm_manager is not False:
            self.swarm_join(swarm_manager, 'worker')
            return True

        print "In order to add a worker node you first need to create a manager node."
        return False


# temporary
def build_infrastucture():
    doctl = Digitalocean(DOCTL, PK_FILE)
    doctl.set_filter_tag('makonda')

    number_of_nodes = int(doctl.get_number_of_nodes('manager')) + int(doctl.get_number_of_nodes('worker'))
    if int(number_of_nodes) == 0:
        print 'Swarm does not exist, creating a new one.'
        doctl.add_manager()
        return True
    # worker_status = doctl.add_worker()
    # if worker_status is False:
    #    doctl.add_manager()


def main():
    start_time = time.time()
    build_infrastucture()
    end_time = time.time()
    print 'Time elapsed: {0}s'.format(end_time - start_time)


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
