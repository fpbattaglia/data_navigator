import inspect
import os
import re
from collections import OrderedDict
from src.config import project_metadata, project_dir

oe_continuous = r'\d+_CH(?P<channel>\d+)(_((\d+)|merged))*.continuous'


def check_target_level_validity(levels, names):
    level_target = OrderedDict()
    for n, v in levels.items():
        if n not in names:
            raise ValueError("no level named {}".format(n))

    for i in range(len(levels)):
        if names[i] not in levels:
            raise ValueError("Invalid levels: " + str(levels))
        level_target[names[i]] = levels[names[i]]
    return level_target


def levels_match(level, level_target):
    match = True
    for n, v in level_target.items():
        if level[n] != v:
            match = False
    return match


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


def _walk(top, maxdepth, total_depth):
    dirs, nondirs = [], []
    for entry in os.scandir(top):
        (dirs if entry.is_dir() else nondirs).append(entry.path)
    if maxdepth == 0:
        levels = []
        t = top
        for _ in range(total_depth):
            (t, l) = os.path.split(t)
            levels.append(l)
        levels = levels[::-1]
        yield top, levels, dirs, nondirs
    if maxdepth > 0:
        for path in dirs:
            for x in _walk(path, maxdepth - 1, total_depth):
                yield x


def rebase_pathname(d, head_d, new_d):
    all_base = []
    head = d
    while os.path.realpath(head) != os.path.realpath(head_d):
        (head, tail) = os.path.split(head)
        all_base.insert(0, tail)

    return os.path.join(new_d, *all_base)


class Cursor:
    def __init__(self, levels, dir_, file, nav, attr=None):
        self.levels = levels
        self.__dict__.update(levels)
        self.d = dir_
        self.n = file
        self.nav = nav
        if attr:
            self.attr = attr
            self.__dict__.update(attr)
        else:
            self.attr = {}

    @property
    def preproc_d(self):
        return rebase_pathname(self.d, self.nav.head_d, self.nav.preproc_d)


class CursorDir(Cursor):
    def __init__(self, levels, dir_, files=None, nav=None):
        super().__init__(levels=levels, dir_=dir_, file=files, nav=nav, attr=None)

        self.files = []
        if files:
            for fn in files:
                if isinstance(fn, str):
                    fn = Cursor(self.levels, self.d, fn, self.nav)
                elif not isinstance(fn, Cursor):
                    raise ValueError("files must contain either file names or Cursor objects")
                self.files.append(fn)
        else:
            filenames = []
            for (d, _, f) in os.walk(dir_):
                filenames.extend([os.path.join(d, ff) for ff in f if ff is not '.'])
                self.files = [Cursor(self.levels, self.d, fn, self.nav) for fn in filenames]
        self.n = [c.n for c in self.files]

    def get_files(self, pattern):
        file_list = []
        for fn in self.files:
            m = re.match(pattern, os.path.basename(fn.n))
            if m:
                file_list.append(Cursor(self.levels, self.d, fn.n, self.nav, m.groupdict()))
        return CursorDir(self.levels, self.d, file_list, self.nav)

    def __iter__(self):
        return iter(self.files)


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
        self.level_names = metadata["levels"].split(',')
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

    def cursor_dir(self, **kwargs):
        levels_target = check_target_level_validity(kwargs, self.level_names)
        dir_ = os.path.join(self.head_d, *(levels_target.values()))
        return CursorDir(levels_target, dir_, nav=self)

    def iter(self, level=None, pattern=None, do_groups=False, **kwargs):
        if level is None:
            level = self.level_names[-1]

        # check validity of levels
        level_target = check_target_level_validity(kwargs, self.level_names)

        depth = self.level_names.index(level) + 1
        top_dir = self.head_d
        for top, levels_, dirs_, files in _walk(top_dir, depth, depth):
            levels_dict = {name: level_ for (name, level_) in zip(self.level_names, levels_)}
            if level_target and not levels_match(levels_dict, level_target):
                continue
            if pattern is None:
                yield CursorDir(levels=levels_dict, dir_=top, files=files, nav=self)
            elif do_groups:
                file_list = []
                for fn in files:
                    m = re.match(pattern, os.path.basename(fn))
                    if m:
                        file_list.append(fn)
                yield CursorDir(levels=levels_dict, dir_=top, files=file_list, nav=self)
            else:
                for fn in files:
                    m = re.match(pattern, os.path.basename(fn))
                    if m:
                        yield Cursor(levels=levels_dict, dir_=top, file=fn, nav=self, attr=m.groupdict())

    def iter_groups(self, level, pattern=None, **kwargs):
        yield from self.iter(level, pattern, do_groups=True, **kwargs)


if __name__ == '__main__':
    for top_, all_levels, all_dirs, files_ in _walk('/Users/fpbatta/src/batlab/data_navigator/data/raw/', 2, 2):
        print('top_: ', top_)
        print('all_levels: ', all_levels)
        print('all_dirs: ', all_dirs)
        print('files: ', files_)
