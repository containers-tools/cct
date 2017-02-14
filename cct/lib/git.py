import logging
import os
import subprocess

from cct.errors import CCTError

logger = logging.getLogger('cct')

def clone_repo(url, path, version=None):
    try:
        if not os.path.exists(path):
            logger.info("cloning %s into %s" %(url, path))
            subprocess.check_call(["git", "clone", url, path])
            if version:
                logger.info('Checking out %s revision' %version)
                subprocess.check_call(['git', 'checkout', version], cwd=path)
    except Exception as ex:
        logger.error("cannot clone repo %s into %s: %s", url, path, ex)
        raise CCTError('Cannot clone repo %s, %s' % (url, ex))

