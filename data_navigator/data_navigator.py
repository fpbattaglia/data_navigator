import inspect
import os

from src.config import project_metadata, project_dir


def get_caller(back=1):
    """
    get the main parameters of a calling function
    :param back: how many frames back in the stack you should go
    :return: a dict with fields 'filename', 'lineno', and 'function'
    """
    frame_caller = inspect.stack()[back]
    caller = {'filename': frame_caller[1], 'lineno': frame_caller[2],
              'function': frame_caller[3]}
    return caller


def get_current_file():
    return __file__


def get_project_directory():
    return os.path.abspath(os.path.join(get_current_file(), os.pardir, os.pardir))


def walk(top, maxdepth):
    dirs, nondirs = [], []
    for entry in os.scandir(top):
        (dirs if entry.is_dir() else nondirs).append(entry.path)
    yield top, dirs, nondirs
    if maxdepth > 1:
        for path in dirs:
            for x in walkMaxDepth(path, maxdepth-1):
                yield x


class Cursor:
    pass  # TODO


class CursorDir:
    pass  # TODO

class DataNavigator:
    def __init__(self, dir_=None, metadata=None):

        # caller_dir = os.path.abspath(os.path.join(get_caller(back=2)['filename'], os.pardir))

        # self.caller = get_caller(back=2)
        # self.caller_dir = caller_dir
        if dir_:
            self.project_dir = dir_
        else:
            self.project_dir = project_dir
        if metadata:
            self.metadata = metadata
        else:
            self.metadata = project_metadata

        self.raw_d = os.path.join(self.project_dir, 'data', 'raw')
        self.preproc_d = os.path.join(self.project_dir, 'data', 'preprocessed')
        self.interm_d = os.path.join(self.project_dir, 'data', 'intermediate')
        self.results_d = os.path.join(self.project_dir, 'data', 'results')
        self.depth = metadata['depth_directory_structure']
        self.levels = metadata["levels"].split(',')
        self.head_d = self.raw_d
        self.navigate_results = False
        # TODO self.raw, self.results, self.figures, self.preproc, self.interm are copies of the data navigator and eg
        # results etc have suffixes for the iterator
        # TODO a navigator (this) an iterator (walking through folders) and a cursor providing substitutions etc.

    def raw_navigator(self):
        nav = DataNavigator(self.project_dir, self.metadata)
        nav.head_d = self.raw_d
        return nav

    def preproc_navigator(self):
        nav = DataNavigator(self.project_dir, self.metadata)
        nav.head_d = self.preproc_d
        return nav

    def interm_navigator(self):
        nav = DataNavigator(self.project_dir, self.metadata)
        nav.head_d = self.interm_d
        return nav

    def results_navigator(self):
        nav = DataNavigator(self.project_dir, self.metadata)
        nav.head_d = self.results_d
        return nav


if __name__ == '__main__':
    print(get_caller())
    print(get_current_file())
