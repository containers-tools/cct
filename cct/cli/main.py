"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.
"""

import argparse
import logging
import yaml

from cct import setup_logging
from cct.change_processor import ChangeProcessor
from cct.module import Operation, ModuleRunner, Module
logger = logging.getLogger('cct')

class CCT_CLI(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        
    def setup_arguments(self):
        self.parser.add_argument('-v', '--verbose', action="store_true", help='verbose output')
        self.parser.add_argument('-q', '--quiet', action="store_true", help='set quiet output')
        self.parser.add_argument('method', nargs='*', help='run one module from command line')

    def run(self):
        self.setup_arguments()
        args = self.parser.parse_args()
        if args.verbose:
            setup_logging(level=logging.DEBUG)
        elif args.quiet:
            setup_logging(level=logging.ERROR)
        else:
            setup_logging(level=logging.INFO)
        try:
            #POC Implementation
            if args.method[0] == 'run':
                module = args.method[1]
                operation = Operation(args.method[2], args.method[3:])
                module = Module(module, [operation])
                runner = ModuleRunner(module)
                runner.run()
            if args.method[0] == 'process':
            #POC Implementation
                filename = args.method[1]
                stream = open(filename, 'r')
                change = yaml.load(stream)
                cp = ChangeProcessor(change)
                cp.process()

        except KeyboardInterrupt:
            pass
        except Exception as ex:
            if args.verbose:
                raise
            else:
                logger.error("Exception caught: %s", repr(ex))
    
if __name__ == '__main__':
    cli=CCT_CLI()
    cli.run()
