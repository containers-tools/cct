"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""
import os
import shutil

from cct.module import Module
from cct.lib.file_utils import create_dir

class File(Module):

    def copy(self, source, destination):
        """
        Copies file.

        Args:
            source: path to file
            destination: path where file should be copied
        """
        self.create_dir(destination)
        shutil.copy(source, destination)

    def link(self, source, destination):
        """
        Creates symbolik link.

        Args:
            source: path to symbolik link destination
            destination: Symbolik link name
        """
        self.create_dir(destination)
        os.symlink(source, destination)

    def move(self, source, destination):
        """
        Moves file.

        Args:
            source: path to file
            destination: path where file should be moved
        """
        self.create_dir(destination)
        shutil.move(source, destination)

    def remove(self, path):
        """
        Removes file.

        Args:
            source: path to file to be removed
        """
        shutil.rmtree(path)
