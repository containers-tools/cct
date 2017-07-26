"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import argparse
import logging
import os
import pkgutil
import sys
import urllib2
import yaml

from cct import setup_logging, version
from cct.change_processor import ChangeProcessor
from cct.module import ModuleManager

from urlparse import urlparse
from pykwalify.core import Core
from pykwalify.errors import SchemaError

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
        self.parser.add_argument('--modules-dir', nargs='?', default="%s/%s" % (os.getcwd(), 'modules'), help='directory from where modules are executed')
        self.parser.add_argument('--artifacts-dir', nargs='?', default="%s/%s" % (os.getcwd(), 'artifacts'), help='directory where artifacts are stored')
        self.parser.add_argument('-v', '--verbose', action="store_true", help='verbose output')
        self.parser.add_argument('-q', '--quiet', action="store_true", help='set quiet output')
        self.parser.add_argument('changes', help='YAML files to process', nargs="*")
        self.parser.add_argument('-l', '--list', help='list all modules', action="store_true")
        self.parser.add_argument('-s', '--show', help='show module usage')
        self.parser.add_argument('-c', '--command', help="exec this command after processing changes", nargs=argparse.REMAINDER)
        self.parser.add_argument('-g', '--get-changes', help="download a list of changes from url")
        self.parser.add_argument('--version', action='version', help="show version", version=version.version)

    def exec_command(self, command):
        if command[1:]:
            logger.info("executing command %s with args %s" % (command[0], " ".join(command[1:])))
        else:
            logger.info("executing command %s" % command[0])
        os.execvp(command[0], command)

    def process_url(self, url):
        response = urllib2.urlopen(url)
        return yaml.load(response.read())

    def process_file(self, file):
        stream = open(file, 'r')
        return yaml.load(stream)

    def process_changes(self, changes, modules_dir, artifacts_dir):
        schema = yaml.safe_load(pkgutil.get_data('cct', 'schema.yaml'))
        for change in changes:
            if change is '':
                continue
            scheme = urlparse(change).scheme
            if 'http' in scheme:
                change = self.process_url(change)
            else:
                change = self.process_file(change)

            c = Core(source_data=change, schema_data=schema)
            try:
                c.validate(raise_exception=True)
            except SchemaError as e:
                logger.error('CCT change viloates schema, %s', e)
                raise e
            cp = ChangeProcessor(change, modules_dir, artifacts_dir)
            return cp.process()

    def run(self):
        self.setup_arguments()
        env_changes = None
        changes = []
        try:
            env_changes = os.environ['CCT_CHANGES']
        except KeyError:
            pass
        if len(sys.argv) < 2:
            self.parser.print_help()
            sys.exit(1)
        args = self.parser.parse_args()
        if args.get_changes:
            changes += urllib2.urlopen(args.get_changes).read().split('\n')
        if args.verbose:
            setup_logging(level=logging.DEBUG)
        elif args.quiet:
            setup_logging(level=logging.ERROR)
        else:
            setup_logging(level=logging.INFO)
        modules = ModuleManager(args.modules_dir, args.artifacts_dir)
        if args.list:
            modules.discover_modules()
            modules.list()
        elif args.show:
            modules.discover_modules()
            modules.list_module_oper(args.show)
        else:
            # env changes overrides cmdline ones
            # seems odd but really needed for containers - changes are passed
            # via docker run -e
            if env_changes:
                changes += env_changes.split()
            else:
                changes += args.changes
            try:
                self.process_changes(changes, args.modules_dir, args.artifacts_dir)
            except KeyboardInterrupt:
                pass
            except Exception:
                logger.error("CCT failed, check logs above for errors")
                exit(1)
        if args.command:
            self.exec_command(args.command)


def run():
    cli = CCT_CLI()
    cli.run()

if __name__ == '__main__':
    run()
