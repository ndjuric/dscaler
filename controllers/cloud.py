#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time

from config import *
from .digitalocean import Digitalocean
from .docker import Docker
from .ssh import SSH


class Cloud(SSH):
    def __init__(self, tag, swarm_dir=SWARM_DIR, script_create=SCRIPT_CREATE, script_join=SCRIPT_JOIN):
        """ Cloud orchestration class. """
        super(Cloud, self).__init__()
        self.doctl = Digitalocean(DOCTL, PK_FILE, tag)
        self.docker = Docker()

        self.swarm_dir = swarm_dir
        self.script_create = script_create
        self.script_join = script_join

        if not os.path.exists(swarm_dir):
            os.makedirs(swarm_dir)

    def build(self):
        """ Build a seed swarm. Same VM is both manager and a worker. """
        number_of_nodes = int(self.doctl.get_number_of_droplets_by_tag('manager'))
        number_of_nodes += int(self.doctl.get_number_of_droplets_by_tag('worker'))
        if int(number_of_nodes) == 0:
            print('Swarm does not exist, creating a new one.')
            self.add_manager()
            return True
        print('Swarm already exists.')

    def destroy(self):
        """ Destroy everything!!! """
        self.doctl.destroy_droplets()

    def deploy(self):
        """ Redeploy the projects, takes about ~25 seconds. """
        manager = self.doctl.get_single_droplet_by_tag('manager')
        self.docker.swarm_deploy(manager['ip'])

    def generate_swarm_join_script(self, swarm_key, droplet_ip):
        """ Generate a swarm join script and write it to a file. """
        join_script_path = self.swarm_dir + '/join.sh'
        fh = open(join_script_path, 'w')
        fh.write(self.script_join.format(swarm_key, droplet_ip))
        fh.close()
        return join_script_path

    def generate_swarm_create_script(self):
        """ Generate a swarm create script and write it to a file. """
        create_script_path = self.swarm_dir + '/create.sh'
        fh = open(create_script_path, 'w')
        fh.write(self.script_create)
        fh.close()
        return create_script_path

    def swarm_join(self, manager, node_type='worker'):
        """ Swarm join functionality, this needs to be refactored"""
        swarm_key = self.docker.get_swarm_key(manager['ip'], node_type)

        boot_script_path = self.generate_swarm_join_script(swarm_key, manager['ip'])

        print("Joining an existing swarm: {0}@{1} (takes about a minute)".format(manager['name'], manager['ip']))

        self.doctl.create_droplet(node_type, boot_script_path)
        return True

    def add_manager(self):
        """ Use provided tag to lookup swarm status. 
        If there's no swarm bring up a VM and set it up as a swarm manager."""
        node_type = "manager"
        manager = self.doctl.get_single_droplet_by_tag(node_type)

        if manager is not False:
            self.swarm_join(manager, node_type)
            return True

        boot_script_path = self.generate_swarm_create_script()
        print("Creating a new swarm host (takes about a minute)...")
        self.doctl.create_droplet(node_type, boot_script_path, wait=True)
        return True

    def add_worker(self):
        """ Add a worker VM to Digitalocean. Use provided tag to join a swarm, if swarm manager VM exists. """
        manager = self.doctl.get_single_droplet_by_tag('manager')

        if manager is not False:
            self.swarm_join(manager, 'worker')
            return True

        print("In order to add a worker node you first need to create a manager node.")
        return False

    def remove_worker(self):
        """ Remove a random swarm worker and destroy the droplet where it was located. """
        node_type = 'worker'
        worker_info = self.doctl.get_single_droplet_by_tag(node_type)
        if not worker_info:
            print("Worker removal failed, there are no workers tagged \"{0}\"".format(self.doctl.tags[node_type]))
        else:
            print("Leaving the swarm...")
            self.docker.drain_containers(worker_info['ip'], worker_info['name'])
            time.sleep(2)
            self.docker.remove_node(worker_info['ip'], worker_info['name'])
            self.doctl.purge_droplet(worker_info['name'])

    def remove_manager(self):
        """ Remove the swarm manager and destroy the droplet where it was located
        (at least 2 managers needed for this). """
        node_type = 'manager'
        number_of_managers = self.doctl.get_number_of_droplets_by_tag(node_type)

        if int(number_of_managers) < 2:
            print("You need at least 2 managers in order to remove 1 manager.")
            return False

        manager_info = self.doctl.get_single_droplet_by_tag(node_type)
        if not manager_info:
            print("Node removal failed, there are no nodes tagged \"{0}\"".format(self.doctl.tags[node_type]))
            return False

        print("Leaving the swarm...")
        self.docker.drain_containers(manager_info['ip'], manager_info['name'])
        time.sleep(2)
        self.docker.demote_manager(manager_info['ip'], manager_info['name'])
        self.doctl.purge_droplet(manager_info['name'])

    def ssh_manager(self):
        """ SSH to a swarm manager. """
        manager_info = self.doctl.get_single_droplet_by_tag('manager')
        if not manager_info:
            print('SSH failed, there are no managers in this swarm. Does the swarm exist???')
            return False

        print("ssh -o \"StrictHostKeyChecking no\" %s@%s" % ('root', manager_info['ip']))
        return True

    def logs_master(self):
        """ Show master cruncher logs from the swarm. """
        manager_info = self.doctl.get_single_droplet_by_tag('manager')
        if not manager_info:
            print('There are no managers in this swarm. Does the swarm exist???')
            return False

        filter_str = 'master'
        containers = self.docker.get_containers_by_substring(manager_info['ip'], filter_str)
        containers_len = len(containers)
        if containers_len == 0:
            print('No containers found for "{0}"'.format(filter_str))
            return False
        if containers_len > 1:
            print('Multiple containers found for "{0}". There can be only one master.'.format(filter_str))
            return False
        container = containers[0]
        print('"{0}" found in {1}'.format(filter_str, container))
        print(
            "ssh -o \"StrictHostKeyChecking no\" %s@%s \"%s\"" % (
                'root',
                manager_info['ip'],
                'docker logs -f {0}'.format(container)
            )
        )
        # logs = self.remote_exec('root', manager_info['ip'], 'docker logs {0}'.format(container))
        # for line in logs:
        #    print line.rstrip()
