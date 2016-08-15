"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import os
import unittest
import mock

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
            'changes': [{'dummy.Dummy': [{'dump': 493}]}],
            'name': 'dummy'
        }]
        changerunner = ChangeProcessor(config)
        changerunner.process()

if __name__ == '__main__':
    unittest.main()
