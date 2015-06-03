"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.
"""

import argparse
import logging
import yaml
import sys

from cct import setup_logging
from cct.module import Modules
from cct.change_processor import ChangeProcessor
logger = logging.getLogger('cct')

class MyParser(argparse.ArgumentParser):

    def error(self, message):
        self.print_help()
        sys.stderr.write('\nError: %s\n' % message)
        sys.exit(2)


class CCT_CLI(object):
    def __init__(self):
        self.parser = MyParser(description='Container configuration tool')
        
    def setup_arguments(self):
        self.parser.add_argument('-v', '--verbose', action="store_true", help='verbose output')
        self.parser.add_argument('-q', '--quiet', action="store_true", help='set quiet output')
        self.parser.add_argument('files', help='YAML files to process', nargs="*")
        self.parser.add_argument('-l', '--list', help='list all modules', action="store_true")
        self.parser.add_argument('-s', '--show', help='show module usage')

    def run(self):
        self.setup_arguments()
        args = self.parser.parse_args()
        if args.verbose:
            setup_logging(level=logging.DEBUG)
        elif args.quiet:
            setup_logging(level=logging.ERROR)
        else:
            setup_logging(level=logging.INFO)
        if args.list:
            Modules.list()
        elif args.show:
            Modules.list_module_oper(args.show)
        elif args.files:
            try:
                for yaml_file in args.files:
                    stream = open(yaml_file, 'r')
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
        else:
             self.parser.print_help()
    
if __name__ == '__main__':
    cli=CCT_CLI()
    cli.run()
