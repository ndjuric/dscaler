#!/usr/bin/env python3

import time
import json

from controllers import *
from config import CALL_MAP, TAG
from flask import Flask, jsonify, request


class API(object):
    def __init__(self):
        """ Cloud orchestration web API. """
        self.app = Flask(__name__, static_url_path="")
        self.app.add_url_rule('/swarm', 'swarm', self.swarm, methods=['POST'])

        for error in (400, 401, 403, 404, 405, 500):
            self.app.register_error_handler(error, self.http_error_handler)

        self.cloud = CloudInterface(CALL_MAP, TAG)
        self.token = '161831337'

    def run(self):
        """ Run the server. """
        self.app.run(host='0.0.0.0', port=5000, debug=True)

    @staticmethod
    def http_error_handler(error):
        return jsonify({'status': False, 'message': '{0}'.format(error)})

    @staticmethod
    def is_json(json_string):
        try:
            json_object = json.loads(json_string)
        except ValueError, e:
            return False
        return True

    def swarm(self):
        """ Route: /swarm """
        if not self.is_json(request.get_data()):
            return jsonify({'status': False, 'message': 'Invalid json format.'})

        req = json.loads(request.get_data())
        if 'tag' not in req or 'action' not in req or 'token' not in req:
            return jsonify({'status': False, 'message': 'Mandatory fields missing.'})

        tag = req['tag']
        token = req['token']
        action = req['action']

        if token != self.token:
            return jsonify({'status': False, 'message': 'Invalid token.'})

        self.cloud.set_tag(tag)
        status = self.cloud.run(action)

        return jsonify(status)


class CloudInterface(object):
    def __init__(self, call_map, tag):
        self.tag = tag
        self.action = call_map[0]
        self.call_map = call_map

    def set_tag(self, tag):
        self.tag = tag

    def run(self, action):
        start_time = time.time()
        cloud = Cloud(self.tag)
        if cloud:
            print('Cloud control class instantiated.')
        else:
            print('Critical error, try again.')

        instance = 'cloud'
        status = dict()
        if action in self.call_map:
            expression = '{0}.{1}()'.format(instance, action)
            status = eval(expression)

        end_time = time.time()
        status['elapsed'] = '{0}s'.format(end_time - start_time)

        print(status)
        return status


def main():
    api = API()
    api.run()


if __name__ == '__main__':
    CALL_MAP = [
        'build',
        'deploy',
        'destroy',
        'add_worker',
        'add_manager',
        'ssh_manager',
        'logs_master',
        'remove_worker',
        'remove_manager',
        'master_container'
    ]

    main()
