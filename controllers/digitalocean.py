#!/usr/bin/env python3

import time
from .ssh import SSH


class Digitalocean(SSH):
    def __init__(self, doctl_path, public_key_file, tag):
        """ Digitalocean infrastructure management class """
        super(Digitalocean, self).__init__()
        self.doctl = doctl_path
        self.filter_tag = tag
        self.tags = self.set_node_tags()
        self.ssh_key = self.get_local_fingerprint(public_key_file)

    def set_filter_tag(self, tag):
        """ Set the main tag (identifier) of the swarm, ie. name of the company, or name of the project """
        self.filter_tag = tag
        self.set_node_tags()

    def set_node_tags(self):
        """ Set swarm manager and worker tags, suffixes to the main tag of the swarm """
        self.tags = {
            'manager': self.filter_tag + '-manager',
            'worker': self.filter_tag + '-worker'
        }
        return self.tags

    def create_tag(self, node_type='worker'):
        """ Create a digitalocean tag, specified by node_type. """
        if self.filter_tag:
            return self.local_exec('./scripts/create-tag.sh {0}'.format(str(self.tags[node_type])))

        return False

    def list_droplets_by_tag(self, node_type):
        """ List members of the swarm of type node_type (either manager or worker) """
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

    def get_single_droplet_by_tag(self, node_type):
        """ Get a single node of type node_type (either manager or worker) """
        result = self.local_exec('./scripts/swarm-list.sh {0} | head -n1'.format(self.tags[node_type]))
        if not result:
            return False
        node_info = result[0].split()
        node = {
            'name': node_info[0],
            'ip': node_info[1]
        }
        return node

    def get_number_of_droplets_by_tag(self, node_type):
        """ Get number of nodes in the entire swarm for the set tag. """
        result = self.local_exec('./scripts/swarm-list.sh {0} | wc -l'.format(self.tags[node_type]))
        return b''.join(result)

    def destroy_droplets(self):
        """ This one is pretty much straightforward. Destroys the swarm. """
        print('Destroying swarm {0}'.format(self.filter_tag))
        swarm = []
        workers = self.list_droplets_by_tag('worker')
        managers = self.list_droplets_by_tag('manager')

        if workers:
            swarm += workers

        if managers:
            swarm += managers

        for host in swarm:
            self.purge_droplet(host['name'])

    def create_droplet(self, node_type, boot_script_path, wait=False):
        """ Create a new droplet """
        self.create_tag(node_type)
        droplet_name = "{0}-{1}".format(self.tags[node_type], str(time.time()))

        append = ''
        if wait is not False:
            append = '--wait'

        self.local_exec(
            './scripts/add-droplet.sh {0} {1} {2} {3} ./{4}'.format(
                droplet_name,
                append,
                self.tags[node_type],
                self.ssh_key,
                boot_script_path
            )
        )

    def purge_droplet(self, droplet_name):
        """ Purge/destroy a digitalocean droplet. """
        print("Purging droplet {0}...".format(droplet_name))
        return self.local_exec('./scripts/droplet-purge.sh {0}'.format(droplet_name))
