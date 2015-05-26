"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.
"""

import logging

from cct.module import Module
logger = logging.getLogger('cct')

class Dummy(Module):
    def run(self, operation):
        logger.info("dummy module performed %s with args %s" % (operation.command, operation.args ))
