import os
import shutil
from checker import (
    config
)
from unittest import TestCase


class TestCheckerBase(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestCheckerBase, self).__init__(*args, **kwargs)
        config.read('./dev.cfg')

    @classmethod
    def setUpClass(cls):
        test_path = config.get('checker', 'downloads_path')
        shutil.rmtree(test_path, ignore_errors=True)
        if not os.path.isdir(test_path):
            os.mkdir(test_path)

    @property
    def test_dir(self):
        return config.get('checker', 'downloads_path')

    def create_download_file(self, file_name, extension='txt'):
        with open(os.path.join(self.test_dir, f'{file_name}.{extension}'), 'w') as f:
            f.write('test file')


class TestCreateEvent(TestCheckerBase):
    def test_image_downloads(self):
        self.create_download_file('image', 'png')
