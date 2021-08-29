#
# This file is licensed under the Apache License v2.0 with LLVM Exceptions.
# See https://llvm.org/LICENSE.txt for license information.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
#
# (c) Copyright 2021 Xilinx Inc.

import argparse
import os
import shlex
import sys
import shutil

xbridge_found = False #shutil.which("xbridge")
xchesscc_found = False #shutil.which("xchesscc_wrapper")

def parse_args():
    parser = argparse.ArgumentParser(prog='aiecc')
    parser.add_argument('filename',
            metavar="file",
            help='MLIR file to compile')
    parser.add_argument('--sysroot',
            metavar="sysroot",
            default="",
            help='sysroot for cross-compilation')
    parser.add_argument('--tmpdir',
            metavar="tmpdir",
            default="acdc_project",
            help='directory used for temporary file storage')
    parser.add_argument('-v',
            dest="verbose",
            default=False,
            action='store_true',
            help='Trace commands as they are executed')
    parser.add_argument('--vectorize',
            dest="vectorize",
            default=False,
            action='store_true',
            help='Enable MLIR vectorization')
    parser.add_argument('--xbridge',
            dest="xbridge",
            default=xbridge_found,
            action='store_true',
            help='Link using xbridge')
    parser.add_argument('--no-xbridge',
            dest="xbridge",
            default=not xbridge_found,
            action='store_false',
            help='Link using peano')
    parser.add_argument('--xchesscc',
            dest="xchesscc",
            default=xchesscc_found,
            action='store_true',
            help='Compile using xchesscc')
    parser.add_argument('--no-xchesscc',
            dest="xchesscc",
            default=not xchesscc_found,
            action='store_false',
            help='Compile using peano')
    parser.add_argument("arm_args",
            action='store',
            help='arguments for ARM compiler',
            nargs=argparse.REMAINDER)

    opts = parser.parse_args(sys.argv[1:])

    return opts


def _positive_int(arg):
    return _int(arg, 'positive', lambda i: i > 0)


def _non_negative_int(arg):
    return _int(arg, 'non-negative', lambda i: i >= 0)


def _int(arg, kind, pred):
    desc = "requires {} integer, but found '{}'"
    try:
        i = int(arg)
    except ValueError:
        raise _error(desc, kind, arg)
    if not pred(i):
        raise _error(desc, kind, arg)
    return i


def _case_insensitive_regex(arg):
    import re
    try:
        return re.compile(arg, re.IGNORECASE)
    except re.error as reason:
        raise _error("invalid regular expression: '{}', {}", arg, reason)


def _error(desc, *args):
    msg = desc.format(*args)
    return argparse.ArgumentTypeError(msg)