#!/bin/python
import os

from zipfile import ZipFile

with ZipFile('cct.zip', 'w') as zf:
    zf.write('__main__.py')
    for root, directory, files in os.walk('cct'):
        for f in files:
            arc_file = os.path.join(root, f)
            zf.write(arc_file)
