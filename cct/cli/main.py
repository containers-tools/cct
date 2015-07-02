"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.
"""

import argparse
import logging
import yaml
import os
import shlex
import sys
import urllib2

from cct import setup_logging, version
from cct.module import Modules
from cct.change_processor import ChangeProcessor
from urlparse import urlparse
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
        self.parser.add_argument('changes', help='YAML files to process', nargs="*")
        self.parser.add_argument('-l', '--list', help='list all modules', action="store_true")
        self.parser.add_argument('-s', '--show', help='show module usage')
        self.parser.add_argument('-c', '--command', help="exec this command after processing changes")
        self.parser.add_argument('--version', action='version', help="show version", version=version.version)

    def exec_command(self, command):
        command = shlex.split(command)
        if command[1:]:
            logger.info("executing command %s with args %s" %(command[0], " ".join(command[1:])))
        else:
            logger.info("executing command %s" %command[0])
        os.execvp(command[0], command)

    def process_url(self, url):
        response = urllib2.urlopen(url)
        change = yaml.load(response.read())
        cp = ChangeProcessor(change)
        cp.process()

    def process_file(self, file):
        stream = open(file, 'r')
        change = yaml.load(stream)
        cp = ChangeProcessor(change)
        cp.process()

    def process_changes(self, changes):
        for change in changes:
            scheme = urlparse(change).scheme
            if scheme == 'http':
                self.process_url(change)
            else:
                self.process_file(change)

    def run(self):
        self.setup_arguments()
        env_changes=None
        try:
            env_changes = os.environ['CCT_CHANGES']
        except KeyError:
            pass
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
        elif args.changes or env_changes:
            changes = []
            ## env changes overides cmdline ones
            ## seems odd but really needed for containers - changes are passed
            ## via docker run -e
            if env_changes:
                changes += env_changes.split()
            else:
                changes += args.changes
            try:
                self.process_changes(changes)
            except KeyboardInterrupt:
                pass
            except Exception as ex:
                if args.verbose:
                    raise
                else:
                    logger.error("Exception caught: %s", repr(ex))
        if args.command:
            self.exec_command(args.command)
def run():
    cli=CCT_CLI()
    cli.run()

if __name__ == '__main__':
    run()
