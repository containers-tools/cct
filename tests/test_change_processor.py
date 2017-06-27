"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import unittest
import shutil
import tempfile

from cct.change_processor import ChangeProcessor


class TestModule(unittest.TestCase):

    def test_process_string_values(self):
        """
        Make sure that changes that have string values are accepted
        """
        config = [{
            'changes': [{'base.Dummy': [{'dump': '493'}]}],
            'name': 'dummy',
            'modules': [{'url': 'tests/modules/'}]
        }]
        changeProcessor = ChangeProcessor(config, 'tests/modules', '/tmp')
        changeProcessor.process()

    def test_process_int_values(self):
        """
        Make sure that changes that have integer values are accepted
        """
        config = [{
            'changes': [{'base.Dummy': [{'dump': 493}, {'dump': 'foo'}]},
                        {'base.Dummy': [{'dump': 567}]},
                        {'base.Dummy': [{'dump': 123}]}],
            'name': 'dummy',
            'modules': [{'url': 'tests/modules/'}]
        }]
        changeProcessor = ChangeProcessor(config, 'tests/modules', '/tmp')
        changeProcessor.process()

    def test_fetch_modules(self):
        config = [{
            'changes': [{'base.Dummy': [{'dump': 493}]},
                        {'base.Shell': [{'shell': 'echo'}]}],
            'name': 'dummy',
            'modules': [{'url': 'https://github.com/containers-tools/base'}]
        }]
        destination = tempfile.mkdtemp()
        changeProcessor = ChangeProcessor(config, destination, '/tmp/')
        changeProcessor.process()
        shutil.rmtree(destination)

if __name__ == '__main__':
    unittest.main()
