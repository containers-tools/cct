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
        logger.info("dummy module performed dump with args %s and environment: %s" % (args, self.environment))
