# -*- coding: utf-8 -*-
'''Standardization of modification to management commands.'''


import logging
import os
import subprocess
import re
import string

import django.core.management.base

import vedm.util.file


class CustomCommand(django.core.management.base.BaseCommand):
    '''A command that uses Django's verbosity for general logging.'''

    def handle(self, **kwargs):
        '''Adapt Django's standard verbosity argument for general use.'''
        logging.basicConfig(level=10 * (4 - kwargs['verbosity']))


class RawTextCommand(CustomCommand):
    '''A command that edits raw text (YAML) document files.'''

    help = 'Edit raw text'

    _default_folder = None
    _file_prefix = None
    _model = None
    _filename_character_whitelist = string.ascii_letters + string.digits

    def add_arguments(self, parser):
        parser.add_argument('--folder',
                            help='Act on non-default folder'),
        parser.add_argument('--file',
                            help='Act on single file instead of full folder'),
        parser.add_argument('--add', metavar='FILENAME_FRAGMENT',
                            help='Create new file'),
        parser.add_argument('--standardize', action='store_true',
                            help='Batch preparation for revision control'),
        parser.add_argument('--wrap', action='store_true',
                            help='Split long paragraphs for readability'),
        parser.add_argument('--unwrap', action='store_true',
                            help='Join long paragraphs into single lines')

    def handle(self, *args, folder=None, file=None, add=None,
               wrap=False, unwrap=False, standardize=False, **kwargs):
        super().handle(**kwargs)

        if standardize:
            unwrap = wrap = True
            add = False

        if add:
            filepath = os.path.join(folder or self._default_folder, add)

            self._write_new_file(filepath)
            subprocess.call(['gvim', filepath])
            return

        needs_read = any((wrap, unwrap))
        needs_write = any((wrap, unwrap))

        for file in self._get_files(folder, file):
            if needs_read:
                with open(file, mode='r', encoding='utf-8') as f:
                    data = f.read()
            else:
                continue

            new_yaml = vedm.util.cook.cook(data, model=self._model,
                                           unwrap=unwrap, wrap=wrap)

            if new_yaml and needs_write:
                with open(file, mode='w', encoding='utf-8') as f:
                    f.write(new_yaml)

    def _get_files(self, folder, file, **kwargs):
        return tuple(vedm.util.file.find(folder or self._default_folder,
                                         single_file=file, **kwargs))

    def _new_filepath(self, fragment, folder):
        folder_override, _, filename = os.path.split(fragment)
        if self._file_prefix:
            filename = '_'.join((self._file_prefix, filename))
        filename = '{}.yaml'.format(filename)
        blacklist = r'[^{}]'.format(self._filename_character_whitelist)
        filename = filename.format(re.sub(blacklist, '', filename))
        folder = folder_override or folder or self._default_folder
        return os.path.join(folder, filename)

    def _write_new_file(self, filepath):
        logging.info('Creating {}.'.format(filepath))

        with open(filepath, mode='a', encoding='utf-8') as f:
            self._stub_new_file(f)

    def _stub_new_file(self, open_file):
        pass
