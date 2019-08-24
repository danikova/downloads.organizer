from logging.handlers import RotatingFileHandler
import configparser
import subprocess
import argparse
import logging
import time
import sys
import os

from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer

config = configparser.ConfigParser()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            os.path.join(os.path.dirname(__file__), 'logs', 'default.log'), maxBytes=5*1024*1024, backupCount=3
        )
    ]
)

parser = argparse.ArgumentParser(description='Downloads directory observer.')
parser.add_argument('--config', dest='config', help='.cfg file path.')


class SelfScheduleHandler(RegexMatchingEventHandler):
    handled_extensions = []
    destination_directory = ''

    def __init__(self, home_path, directory_destination, regexes):
        super(SelfScheduleHandler, self).__init__(regexes=regexes)
        self.observe_path = os.path.join(home_path, 'Downloads')
        self.dest_path = os.path.join(home_path, directory_destination)

    @classmethod
    def schedule(cls, observer):
        new_self = cls(
            observer.home_path,
            cls.destination_directory,
            [r'.*\.{}$'.format(_re) for _re in cls.handled_extensions]
        )
        observer.observer.schedule(new_self, new_self.observe_path, recursive=True)
        observer.handler_objects.append(new_self)

    @classmethod
    def send_notify(cls, message):
        original_message = [line.format(dest=cls.destination_directory) for line in message]
        message = ['notify-send', '-i', 'go-down', '-t', '10000'] + original_message
        subprocess.Popen(message)
        logging.info(original_message)

    def dispatch(self, event):
        setattr(event, 'src_path_abs', event.src_path.replace(f'{self.observe_path}/', ''))
        super().dispatch(event)

    def on_created(self, event):
        try:
            if not event.is_directory:
                src_path_abs = event.src_path_abs
                _path, _ext = os.path.splitext(src_path_abs)
                dest_path_abs = f'{_path}{_ext}'
                src_path = os.path.join(self.observe_path, src_path_abs)
                dest_path = os.path.join(self.dest_path, dest_path_abs)
                iteration = 0
                while os.path.isfile(dest_path):
                    iteration += 1
                    dest_path_abs = f'{_path}({iteration}){_ext}'
                    dest_path = os.path.join(self.dest_path, dest_path_abs)
                os.rename(src_path, dest_path)
                self.send_notify(['Download Complete', f'{dest_path_abs}, move to {{dest}}'])
        except Exception as e:
            self.send_notify([str(e)])


class ImageHandler(SelfScheduleHandler):
    handled_extensions = ['jpg', 'png', 'gif', 'webp', 'tiff', 'psd', 'raw', 'bmp', 'jpeg', 'svg']
    destination_directory = 'Pictures'


class MusicHandler(SelfScheduleHandler):
    handled_extensions = ['aa', 'aac', 'aax', 'amr', 'awb', 'dct', 'dss', 'dvf', 'flac', 'm4a', 
                          'm4b', 'mmf', 'mp3', 'mpc', 'msv', 'nmf', 'nsf', 'sln', 'tta', 'voc', 
                          'vox', 'wav', 'wma', 'wv']
    destination_directory = 'Music'


class VideoHandler(SelfScheduleHandler):
    handled_extensions = ['vob', 'TS', '3g2', 'webm', 'mp2', 'avi', 'M2TS', 'roq', 'yuv', 'nsv', 
                          'mng', 'mpeg', 'm4p', 'm4v', 'wmv', 'mkv', 'rmvb', 'MTS', 'rm', 'mpg', 
                          'mpe', '3gp', 'ogv', 'mov', 'mpv', 'asf', 'mp4 ', 'mxf', 'ogg', 'amv', 
                          'f4p', 'gifv', 'qt', 'svi', 'f4v', 'flv', 'f4a', 'f4b', 'drc', 'm2v']
    destination_directory = 'Videos'


class DocumentHandler(SelfScheduleHandler):
    handled_extensions = ['ABW', 'ACL', 'AFP', 'AMI', 'Amigaguide', 'ANS', 'ASC', 'AWW', 'CCF', 
                          'CSV', 'CWK', 'DBK', 'DITA', 'DOC', 'DOCM', 'DOCX', 'DOT', 'DOTX', 'DWD', 
                          'EGT', 'EPUB', 'EZW', 'FDX', 'FTM', 'FTX', 'GDOC', 'HTML', 'HWP', 'HWPML', 
                          'LOG', 'LWP', 'MBP', 'MD', 'ME', 'MCW', 'Mobi', 'NB', 'nb', 'NBP', 'NEIS', 
                          'ODM', 'ODOC', 'ODT', 'OSHEET', 'OTT', 'OMM', 'PAGES', 'PAP', 'PDAX', 'PDF', 
                          'QUOX', 'Radix-64', 'RTF', 'RPT', 'SDW', 'SE', 'STW', 'Sxw', 'TeX', 'INFO', 
                          'Troff', 'TXT', 'UOF', 'UOML', 'VIA', 'WPD', 'WPS', 'WPT', 'WRD', 'WRF', 'WRI', 
                          'xhtml', 'XML', 'XPS', 'xht']
    destination_directory = 'Documents'


class DownloadsObserver(object):
    def __init__(self, src_path):
        self.home_path = src_path
        self.observer = Observer()
        self.handler_objects = []
        self._handler_clases = [
            ImageHandler, MusicHandler, VideoHandler, DocumentHandler
        ] 

    def run(self):
        self._schedule()
        self._start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

    def _start(self):
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

    def _schedule(self):
        for handler_class in self._handler_clases:
            handler_class.schedule(self)


def main(args):
    args = parser.parse_args(args)
    config.read(args.config)
    DownloadsObserver(config.get('checker', 'home_directory')).run()


if __name__ == "__main__":
    main(sys.argv[1:])
