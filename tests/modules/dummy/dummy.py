"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import logging

from cct.module import Module

logger = logging.getLogger('cct')

class Dummy(Module):
    def dump(self, *args):
        """
        Dumps arguments to a logfile.

        Args:
         *args: Will be dumped :).
        """
        logger.info("dummy module performed dump with args %s and environment: %s" % (args, self.environment ))
