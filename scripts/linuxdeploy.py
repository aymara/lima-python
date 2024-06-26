#!/usr/bin/env python


# SPDX-FileCopyrightText: 2016-2018 Lars Pontoppidan
# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT


import argparse
import errno
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile


# Helper functions
def error(s):
    print("ERROR: "+s)
    exit(1)


def warn(s):
    if parsed_args['verbose'] > 1:
        print("WARNING: "+s)


def info(s):
    if parsed_args['verbose'] > 0:
        print("INFO: "+s)


def debug(s):
    if parsed_args['verbose'] > 2:
        print("DEBUG: "+s)


blacklist = [
    'linux-vdso.so.1',
    'ld-linux-x86-64.so.2',
    'libstdc++',
    "libcom_err.so",
    "libcrypt.so",
    "libdl.so",
    "libexpat.so",
    "libfontconfig.so",
    "libgcc_s.so",
    "libglib-2.0.so",
    "libgpg-error.so",
    "libgssapi_krb5.so",
    "libgssapi.so",
    "libhcrypto.so",
    "libheimbase.so",
    "libheimntlm.so",
    "libhx509.so",
    "libICE.so",
    "libidn.so",
    "libk5crypto.so",
    "libkeyutils.so",
    "libkrb5.so",
    "libkrb5.so",
    "libkrb5support.so",
    "liblber-2.4.so.2",  # needed for debian wheezy
    "libldap_r-2.4.so.2",  # needed for debian wheezy
    "libm.so",
    "libp11-kit.so",
    "libpcre.so",
    "libpthread.so",
    "libresolv.so",
    "libroken.so",
    "librt.so",
    "libsasl2.so",
    "libSM.so",
    "libusb-1.0.so",
    "libuuid.so",
    "libwind.so",
    "libz.so",

    #//Delete potentially dangerous libraries
    "libstdc",
    "libgobject",
    "libc.so",

    "libdbus-1.so",

    #// Fix the "libGL error" messages
    "libGL.so",
    "libdrm.so",
]


def merge_dicts(x, y):
    '''Given two dicts, merge them into a new dict as a shallow copy.'''
    z = x.copy()
    z.update(y)
    return z


def which(program):
    '''
    Determine if argument is an executable and return the full path.
    Return None if none of either.
    '''
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def resolve_dependencies(executable):
    return ldd(executable)


def ldd(executable):
    '''Get all library dependencies (recursive) of 'executable' '''
    libs = {}
    return lddr(executable, libs)


def lddr(executable, libs):
    '''Get all library dependencies (recursive) of 'executable' '''
    try:
        output = subprocess.check_output(["ldd", "-r", executable])
    except subprocess.CalledProcessError as e:
        warn("CalledProcessError while running %s. Return code %s - output: %s"
             % (e.cmd, e.returncode, e.output))
        exit(1)
    # print(output.decode())
    output = output.decode().split('\n')

    debug(f"Add input lib: {os.path.basename(executable)} => {executable}")
    output.append(f"{os.path.basename(executable)} => {executable}")
    for line in output:
        split = line.split()
        if len(split) == 0:
            continue

        if [split[0] for black in blacklist if split[0].startswith(black)
                or os.path.basename(split[0]).startswith(black)]:
            debug("'%s' is blacklisted. Skipping..." % (split[0]))
            continue

        if split[0] == 'statically' and split[1] == 'linked':
            debug("'%s' is statically linked. Skipping..."
                  % (os.path.basename(executable)))
            continue

        if len(split) < 3:
            warn("Could not determine path of %s %s for ldd output line '%s'. Skipping..."
                 % (os.path.basename(executable), split, line))
            continue

        so = split[0]
        path = split[2]
        realpath = os.path.realpath(path)

        if not os.path.exists(path):
            debug("Can't find path for %s (resolved to %s). (%s => %s) Skipping..."
                  % (so, path, executable, line))
            continue

        if so not in libs:
            details = {
                'so': so,
                'path': path,
                'realpath': realpath,
                'dependants': set([executable]),
                'type': 'lib'}
            libs[so] = details

            debug("Resolved %s to %s" % (so, realpath))

            libs = merge_dicts(libs, lddr(realpath, libs))
        else:
            libs[so]['dependants'].add(executable)

    return libs


def strip(f):
    if os.path.isfile(f):
        res = subprocess.call(('strip', "-x", f))
        debug("Stripping '%s'" % f)
        if res > 0:
            warn("'strip' command failed with return code '%s' on file '%s'"
                 % (res, f))
        return res
    return 0


def build_appdir(dest_dir, dependencies):

    from distutils.dir_util import copy_tree

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    appdir_libs = 'lib'

    if not os.path.exists(dest_dir+os.sep+appdir_libs):
        os.makedirs(dest_dir+os.sep+appdir_libs)

    for dep in dependencies:
        details = dependencies[dep]

        if details['type'] == 'lib':
            src = details['realpath']
            res = re.match(r"^(.*\.so)\.?", dep).group(1)
            dst = dest_dir+os.sep+appdir_libs+os.sep+res
            debug("Copying library "+dep+": "+src+' -> '+dst)
            shutil.copyfile(src, dst)  # overrides dest no questions asked
            strip(dst)
        else:
            src = details['realpath']
            debug("Unhandled type '%s' (%s)" % (details['type'],))


# Main
if __name__ == "__main__":

    script_path = os.path.dirname(os.path.realpath(__file__)).rstrip(os.sep)

    parser = argparse.ArgumentParser(description='Deploy a Qt application on linux.')

    parser.add_argument('executable', help='Input executable', nargs="+")
    parser.add_argument('-d', '--dest_dir',
                        help="Copy library dependencies into this dir", required=False)
    parser.add_argument('-o', '--output',
                        help="Output dependencies to JSON file. Use '-' for stdout",
                        required=False)
    parser.add_argument('-v', '--verbose',
                        help=('Verbose level <0-3> where 0 = No output. 1 = Info. '
                              '2 = Info+Warnings. 3 = Info+Warnings+Debug'),
                        type=int, default=0)

    parsed_args = vars(parser.parse_args())

    output_file = ''
    if parsed_args['output'] is not None:
        output_file = parsed_args['output']
        output_file = output_file.strip(' \t\n\r')
        if output_file != '-':
            output_file = os.path.abspath(output_file)

    dependencies = {}

    for exe in parsed_args['executable']:
        exe = os.path.realpath(exe)
        info('Executable: '+exe)

        # Sanity exe argument checks
        if not os.path.isfile(exe):
            error("%s doesn't exist" % exe)

        info(f"Resolving shared object dependencies for '{os.path.basename(exe)}'")
        exedeps = resolve_dependencies(exe)

        dependencies = merge_dicts(dependencies, exedeps)

    class SetEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, set):
                return list(obj)
            return json.JSONEncoder.default(self, obj)

    if output_file != '':
        if output_file == "-":
            print(json.dumps(dependencies, indent=2, cls=SetEncoder))
        else:
            with open(output_file, 'w') as outfile:
                json.dump(dependencies, outfile, indent=2, cls=SetEncoder)
            info("Wrote %s dependencies to %s" % (len(dependencies), output_file))

    if parsed_args['dest_dir']:
        build_appdir(parsed_args['dest_dir'], dependencies)
