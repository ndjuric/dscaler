#!/usr/bin/env python3

import subprocess


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
