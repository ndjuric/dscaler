#!/usr/bin/env python3

from .ssh import SSH


class Docker(SSH):
    def __init__(self):
        """ Docker management class """
        super(Docker, self).__init__()

    def swarm_deploy(self, swarm_manager_ip):
        """ Deploy image to the swarm master """
        repo = {
            'master': 'private.docker.registry.example.com:5000/master',
            'worker': 'private.docker.registry.example.com:5000/worker'
        }
        commands = 'docker service scale master=0;'
        commands += 'docker service scale worker=0;'
        commands += 'docker service rm worker;'
        commands += 'docker service rm master;'
        commands += 'docker image rm $(docker image ls -a -q) -f;'
        commands += 'docker container rm $(docker container ls -a -q) -f;'
        commands += 'docker service create --network swarmnet --name master '
        commands += '--mount type=bind,source=/nfs,target=/nfs {0};'.format(repo['master'])
        commands += 'docker service create --network swarmnet --name worker {0}'.format(repo['worker'])

        return self.remote_exec('root', swarm_manager_ip, commands)

    def drain_containers(self, ip, name):
        """ Drain docker containers from a specified droplet IP. """
        print('Drainining containers from {0}@{1}...'.format(name, ip))
        self.remote_exec('root', ip, 'docker node update --availability drain {0}'.format(name))

    def demote_manager(self, ip, name):
        """ Demote a swarm manager to worker, on a specified droplet IP. """
        print('Demoting {0}@{1} to worker...'.format(name, ip))
        self.remote_exec('root', ip, 'docker node demote {0}'.format(name))

    def remove_node(self, ip, name):
        """ Remove a docker node. """
        print('Removing docker node {0}@{1}'.format(name, ip))
        self.remote_exec('root', ip, 'docker node rm {0} -f'.format(name))

    def get_swarm_key(self, ip, node_type):
        """ Get docker swarm key """
        result = self.remote_exec('root', ip, 'docker swarm join-token -q {0}'.format(node_type))
        return ''.join(result)

    def get_containers_by_substring(self, ip, substring):
        """ Get a list of containers filtered by substring. """
        container_output = self.remote_exec('root', ip, 'docker container ls')
        containers = []
        for line in container_output:
            if 'CONTAINER ID' in line:
                continue
            if substring in line:
                details = line.split()
                containers.append(details[0])
        return containers

    def get_master_container(self, ip):
        """ Get master container ID. """
        filter_str = 'master'
        containers = self.get_containers_by_substring(ip, filter_str)
        containers_len = len(containers)
        if containers_len == 0:
            print('No containers found for "{0}"'.format(filter_str))
            return False
        if containers_len > 1:
            print('Multiple containers found for "{0}". There can be only one master.'.format(filter_str))
            return False
        return containers[0]
