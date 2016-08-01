# -*- coding: utf-8 -*-
'''File-related utility functions.'''

import os


def find(root_folder, filter=lambda _: True, single_file=None):
    '''Generate relative paths of asset files with prefix, under a folder.

    If a "single_file" argument is provided, it is assumed to be a relative
    path to a single file. This design is intended for ease of use with a
    CLI that takes both folder and file arguments.

    '''
    if single_file:
        if filter(single_file):
            yield single_file
        return

    for dirpath, _, filenames in os.walk(root_folder):
        for f in filenames:
            if filter(f):
                yield os.path.join(dirpath, f)
