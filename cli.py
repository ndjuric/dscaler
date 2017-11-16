#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time

from controllers import *
from config import CALL_MAP
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
        expression = '{0}.{1}()'.format(instance, action)
        result = eval(expression)
        print(result)

    end_time = time.time()

    print('Time elapsed: {0}s'.format(end_time - start_time))


if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.action not in CALL_MAP:
        print('"{0}" either does not exist or you do not have the permission to execute it.'.format(args.action))
        print('You can execute the following methods: {0}'.format(CALL_MAP))
        sys.exit(1)

    main(args.tag, args.action)
