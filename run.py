#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time

from config import *
from controllers import *
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


def get_parser():
    parse = ArgumentParser(description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter)
    parse.add_argument("-t", "--tag",
                       dest="tag",
                       required=True,
                       help="Tag/name used for infrastructure orchestration.")
    parse.add_argument("-a", "--action",
                       dest="action",
                       required=True,
                       help="Action to execute on the infrastructure.")
    return parse


def main(tag, action):
    start_time = time.time()

    cloud = Cloud(tag)
    if cloud:
        print('Cloud control class instantiated.')
    else:
        print('Critical error, try again.')

    instance = 'cloud'
    if action in CALL_MAP:
        eval('{0}.{1}()'.format(instance, action))

    end_time = time.time()

    print('Time elapsed: {0}s'.format(end_time - start_time))


if __name__ == '__main__':
    CALL_MAP = [
        'build',
        'deploy',
        'destroy',
        'add_worker',
        'add_manager',
        'remove_worker',
        'remove_manager'
    ]

    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    if args.action not in CALL_MAP:
        print('"{0}" action not allowed'.format(args.action))
        print('List of allowed actions: {0}'.format(CALL_MAP))
    main(args.tag, args.action)
