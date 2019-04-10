import unittest
import subprocess
import os
import re
import glob

from src.config import project_dir, project_metadata

import data_navigator as dn


def run_command(command):
    return subprocess.check_output(command, shell=True).decode("utf-8")


class LoopAllSessionsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.proj = dn.DataNavigator(project_dir, project_metadata)

    def testLoopDirectories(self):
        command = 'find ' + self.proj.raw_d + ' -type d -depth 2 | wc'
        n_dirs_target = int(run_command(command).split()[0])

        n_dirs = 0
        for fc in self.proj.iter(level='session', pattern=None):  # no pattern (default) means iterate over directories
            # print(fc.d)
            n_dirs += 1

        self.assertEqual(n_dirs_target, n_dirs)

    def testLoopFiles(self):
        command = 'find ' + self.proj.raw_d + ' -name "*.continuous" | wc'
        n_files_target = int(run_command(command).split()[0])
        # act on single files
        n_files = 0
        for _ in self.proj.iter(level='session', pattern=dn.oe_continuous):
            # print(_.n)
            n_files += 1

        self.assertEqual(n_files_target, n_files)

    def test_preproc_d(self):
        for fc in self.proj.iter(level='session', pattern=dn.oe_continuous):
            dir_ = os.path.dirname(fc.n)
            dir_preproc = dir_.replace("raw", "preprocessed")
            self.assertEqual(os.path.realpath(dir_preproc), os.path.realpath(fc.preproc_d))

    def test_channel(self):
        for fc in self.proj.iter(level='session', pattern=dn.oe_continuous):
            patt = r'100_CH(\d+).*\.continuous'
            chan_target = re.match(patt, os.path.basename(fc.n)).groups()[0]
            chan1 = fc.attr['channel']
            self.assertEqual(chan_target, chan1)

            chan2 = fc.channel
            self.assertEqual(chan2, chan_target)

    def test_1_subject(self):
        command = 'find ' + self.proj.raw_d + '/rat_21 -name "*.continuous" | wc'
        n_files_target = int(run_command(command).split()[0])
        n_files = 0
        for _ in self.proj.iter(level='session', pattern=dn.oe_continuous, subject='rat_21'):
            n_files += 1
        self.assertEqual(n_files_target, n_files)


class IterGroupTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.proj = dn.DataNavigator(project_dir, project_metadata)

    def test_iter_group(self):
        did_touch = False

        for fcl in self.proj.iter_groups(level='session'):
            continuous_files = fcl.get_files(pattern=dn.oe_continuous).n
            # let's single out one session
            if fcl.subject == 'rat_21' and fcl.session == 'rat21jitterafternoonday2_2015-12-08_15-49-21':
                file_names = set(fcl.n)
                file_names_target = {os.path.join(fcl.d, f) for f in {'100_CH12.continuous', '100_CH13.continuous',
                                                                      '100_CH25.continuous', '100_CH9.continuous'}}
                self.assertEqual(file_names_target, file_names)
                did_touch = True

        self.assertTrue(did_touch)

    def test_iter_groups_multi_type(self):
        # act on different files in one folder: when pattern is a list, iter_groups yields a list of cursors
        for fcl in self.proj.iter_groups(level='session'):
            continuous_files = fcl.get_files(pattern=dn.oe_continuous).n
            sleep_files = fcl.get_files(pattern=r'.*.eegstates.mat').n
            if fcl.subject == 'rat_21' and fcl.session == 'rat21_learningbaseline2_2015-12-10_15-24-17':
                continuous_files_target = {os.path.join(fcl.d, f) for f in {'100_CH12.continuous',
                                                                            '100_CH13.continuous',
                                                                            '100_CH25.continuous',
                                                                            '100_CH9.continuous'}}
                self.assertEqual(set(continuous_files), continuous_files_target)
                sleep_files_target = [os.path.join(fcl.d, 'sleep.eegstates.mat')]
                self.assertEqual(sleep_files_target, sleep_files)


class SingleCursorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.proj = dn.DataNavigator(project_dir, project_metadata)

    def test_session_cursor(self):
        fcl = self.proj.cursor_dir(subject='rat_21', session='rat21jittertmaze_2015-12-18_11-37-11')
        files = set(fcl.get_files(pattern=dn.oe_continuous).n)
        files_target = set(glob.glob(os.path.join(fcl.d, '*.continuous')))
        self.assertEqual(files_target, files)
