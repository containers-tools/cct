"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""
import os
import shutil
from pwd import getpwnam
from grp import getgrnam

def create_dir(path):
    if os.path.dirname(path):
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

def chown(path, user=None, group=None, recursive=False):
    if user is None:
        uid = -1
    else:
        uid = getpwnam(user).pw_uid
    if group is None:
        gid = -1
    else:
        gid = getgrnam(group).gr_gid
    if recursive:
        for root, dirs, files in os.walk(path):
            for d in dirs:
                os.chown(os.path.join(path, root, d), uid, gid)
            for f in files:
                os.chown(os.path.join(path, root, f), uid, gid)
    else:
        os.chown(path, uid, gid)

def chmod(path, perm, recursive=False):
    if recursive:
        for root, dirs, files in os.walk(path):
            for d in dirs:
                os.chmod(os.path.join(path, root, d), perm)
            for f in files:
                os.chmod(os.path.join(path, root, f), perm)
    else:
        os.chmod(path, perm)

def find(dirname, dirtest, fileaction):
    """
    find: recursively traverse a filesystem structure, expanding
    directories that pass the supplied dirtest, and applying the
    supplied fileaction to each node.
    """
    for child in os.listdir(dirname):
        fullpath = os.path.join(dirname, child)
        fileaction(fullpath)
        if os.path.isdir(fullpath) and dirtest(child):
            find(fullpath, dirtest, fileaction)
