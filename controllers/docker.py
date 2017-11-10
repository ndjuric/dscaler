#!/usr/bin/env python3

from .ssh import SSH


class Docker(SSH):
    """ Docker management class """

    def __init__(self):
        super(Docker, self).__init__()

    ''' Deploy image to the swarm master '''
    def swarm_deploy(self, swarm_manager_ip):
        repo = {
            'master': 'docker.insocl.com:5000/master',
            'worker': 'docker.insocl.com:5000/worker'
        }
        commands = 'docker service scale master=0;'
        commands += 'docker service scale worker=0;'
        commands += 'docker service rm worker;'
        commands += 'docker service rm master;'
        commands += 'docker image rm $(docker image ls -a -q) -f;'
        commands += 'docker container rm $(docker container ls -a -q) -f;'
        commands += 'docker service create --network {0} --name {1} {2};'.format('swarmnet', 'master', repo['master'])
        commands += 'docker service create --network {0} --name {1} {2}'.format('swarmnet', 'worker', repo['worker'])

        return self.remote_exec('root', swarm_manager_ip, commands)

    ''' Drain docker containers from a specified droplet IP. '''

    def drain_containers(self, ip, name):
        print('Drainining containers from {0}@{1}...'.format(name, ip))
        self.remote_exec('root', ip, 'docker node update --availability drain {0}'.format(name))

    ''' Demote a swarm manager to worker, on a specified droplet IP. '''

    def demote_manager(self, ip, name):
        print('Demoting {0}@{1} to worker...'.format(name, ip))
        self.remote_exec('root', ip, 'docker node demote {0}'.format(name))

    def remove_node(self, ip, name):
        print('Removing docker node {0}@{1}'.format(name, ip))
        self.remote_exec('root', ip, 'docker node rm {0} -f'.format(name))

    ''' get docker swarm key '''
    def get_swarm_key(self, ip, node_type):
        result = self.remote_exec('root', ip, 'docker swarm join-token -q {0}'.format(node_type))
        return ''.join(result)
