"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import os
import unittest
import shutil
import tempfile

from cct.change_processor import ChangeProcessor

class TestModule(unittest.TestCase):
    def setUp(self):
        os.environ['CCT_MODULES_PATH'] = 'tests/modules'

    def test_process_string_values(self):
        """
        Make sure that changes that have string values are accepted
        """
        config = [{
            'changes': [{'dummy.Dummy': [{'dump': '493'}]}],
            'name': 'dummy'
        }]
        changerunner = ChangeProcessor(config)
        changerunner.process()


    def test_process_int_values(self):
        """
        Make sure that changes that have integer values are accepted
        """
        config = [{
            'changes': [{'dummy.Dummy': [{'dump': 493}]},
                        {'dummy.Dummy': [{'dump': 567}]}],
            'name': 'dummy'
        }]
        changerunner = ChangeProcessor(config)
        changerunner.process()

    def test_fetch_modules(self):
        config = [{
            'changes': [{'dummy.Dummy': [{'dump': 493}]},
                        {'base.Shell':  [{'shel': 'echo'},
                                         {'url': 'https://github.com/containers-tools/base'}]}],
            'name': 'dummy'
        }]
        destination = tempfile.mkdtemp()
        print(destination)
        changerunner = ChangeProcessor(config)
        changerunner.fetch_modules(config, destination)
        shutil.rmtree(destination)

if __name__ == '__main__':
    unittest.main()
