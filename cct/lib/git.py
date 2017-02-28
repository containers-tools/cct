import logging
import os
import subprocess

from cct.errors import CCTError

logger = logging.getLogger('cct')


def clone_repo(url, path, version=None, force=False):
    try:
        if not os.path.exists(path):
            logger.info("Cloning %s into %s" % (url, path))
            subprocess.check_call(["git", "clone", url, path])
            if version:
                logger.info('Checking out %s revision' % version)
                subprocess.check_call(['git', 'checkout', version], cwd=path)
        elif os.path.exists(path) and force:
            logger.info('Forcing %s revision for %s' % (version, path))
            subprocess.check_call(['git', 'checkout', version], cwd=path)

    except Exception as ex:
        logger.error("Cannot clone repo %s into %s: %s", url, path, ex)
        raise CCTError('Cannot clone repo %s, %s' % (url, ex))


def get_tag_or_branch(path):
    version = None
    # try to get tag first
    try:
        version = subprocess.check_output(['git', 'describe', '--tags', '--exact-match'], stderr=subprocess.STDOUT, cwd=path)
        return version
    except:
        pass
    # if there is no tag return branch
    try:
        version = subprocess.check_output(['git', 'name-rev', '--name-only', 'HEAD'], stderr=subprocess.STDOUT, cwd=path)
    except:
        pass
    return version
