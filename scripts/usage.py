# TODO convention: all data files are *always* referred to as full path names and

import os
import src.data_navigator as dn

from src.config import project_dir, project_metadata


def do_something(fd):
    return 1


proj = dn.DataNavigator(project_dir, project_metadata)


# loop over all session directories
for fc in proj.iter(level='session', pattern=None): # no pattern (default) means iterate
    print(fc.d)

# act on single files
for fc in proj.iter(level='session', pattern=dn.oe_continuous):
    fd = open(fc.n)  # fc.n is a full path name for the file
    result = do_something(fd)
    # getting the channel (encoded in the pattern regex)
    channel = fc.attr['channel']
    # but also
    channel = fc.channel

    # save it in the preprocessed directory. The cursor fc "knows" the right directory for the preprocessed data
    res_file = os.path.join(fc.preproc_d, "someresult_ch" + fc.channel + '.dat')

    result.write(res_file)

# act on single files but only for one subject
for fc in proj.iter(level='session', pattern=dn.oe_continuous, subject='rat_21'):
    print(fc.n)

# act on file groups in the preprocessed folder

preproc_nav = proj.preproc_navigator()
pattern = 'someresult_ch(?P<channel>\d+).dat'

for fcl in preproc_nav.iter_groups(level='session', pattern=dn.oe_continuous):
    file_names = fcl.n  # list of full path names
    channels = [fc.channel for fc in fcl]
    result = do_something(file_names, channels)
    # the directory where they live in
    dir_d = fcl.d
    res_file = os.path.join(fcl.results_d + 'something')

# act on different files in one folder: when pattern is a list, iter_groups yields a list of cursors
for fcl in preproc_nav.iter_groups(level='session'):
    continuous_files = fcl.get_files(pattern=dn.oe_continuous).n
    ripples_files = fcl.get_files(pattern=dn.oe_ripples).n

# act on different files from different repertoires
for fcl in preproc_nav.iter_groups(level='session'):
    continuous_files = fcl.get_files(pattern=dn.oe_continuous).n
    lfp_files = fcl.get_files(pattern=dn.oe_continuous, repertoire=dn.raw).n


# make a cursor just for one session
fcl = preproc_nav.cursor_dir(subject='rat_21', session='22221')

# make a cursor just for one file
fc = preproc_nav.cursor(subject='rat_21', session='22222', file='100_ch21.continuous')
# or
fc = preproc_nav.cursor(subject='rat_21', session='22222', pattern=dn.oe_continuous, channel=21)

open(fc.n)
