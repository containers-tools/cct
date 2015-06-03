"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""
import os
import shutil

from cct.module import Module


class File(Module):

    def create_dir(self, path):
        if os.path.dirname(path):
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))

    def copy(self, source, destination):
        self.create_dir(destination)
        shutil.copy(source, destination)

    def link(self, source, destination):
        self.create_dir(destination)
        os.symlink(source, destination)

    def move(self, source, destination):
        self.create_dir(destination)
        shutil.move(source, destination)
