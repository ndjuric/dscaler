#!/usr/bin/env python3

from .command import Command


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
