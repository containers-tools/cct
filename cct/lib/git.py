import logging
import os
import shutil
import subprocess

from cct.errors import CCTError

logger = logging.getLogger('cct')


def clone_repo(url, path, version=None, force=False):
    # this is not a nice way, but we are passing version as a None explictly on multiple places
    if not version:
        version = "master"
    try:
        if os.path.exists(path):
            if force:
                logger.info("Removing old module from path: '%'." % path)
                shutil.rmtree(path)
            else:
                return

        logger.info("Cloning %s into %s" % (url, path))
        cmd = ["git", "clone", "--depth", "1", url, path, "-b", version]
        logger.debug("Running '%s'" % ' '.join(cmd))
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)

    except Exception as ex:
        logger.error("Cannot clone repo %s into %s: %s", url, path, ex)
        raise
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
