#!/usr/bin/env python3

import argparse
import logging
import os
import subprocess
import sys
import yaml


logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)


def run_cmd(cmd):
    LOG.debug(subprocess.list2cmdline(cmd))
    subprocess.check_call(cmd)


def unpack(src_iso, dest_dir):
    '''
    Unpacks an iso image to the destination directory.
    '''
    LOG.info('Unpack %s to %s' % (src_iso, dest_dir))
    mnt_point = 'tmp/ubuntu-16-server-iso-mnt-point'
    run_cmd(['mkdir', '-p', mnt_point])
    run_cmd(['sudo', 'mount', '-o', 'loop', src_iso, mnt_point])
    run_cmd(['rm', '-rf', dest_dir])
    run_cmd(['cp', '-r', mnt_point, dest_dir])
    run_cmd(['chmod', '-R', 'u+w', dest_dir])
    run_cmd(['sudo', 'umount', mnt_point])


def pack(src_dir, dest_iso):
    '''
    Packs a directory into an iso image.

    Use isohybrid to post-process the generated iso image so that it can be
    dd'ed to usb stick to make a bootable usb stick.
    '''
    LOG.info('Generating %s from directory %s' % (dest_iso, src_dir))
    run_cmd(['mkisofs', '-D', '-r', '-V', 'ATTENDLESS_UBUNTU', '-cache-inodes',
            '-J', '-l', '-b', 'isolinux/isolinux.bin', '-c',
            'isolinux/boot.cat', '-no-emul-boot', '-boot-load-size', '4',
            '-boot-info-table', '-o', dest_iso, src_dir])
    run_cmd(['isohybrid', dest_iso])


def modify(tmp_dir):
    '''
    Modify the files of the iso to make it auto-install.

    The file map is read from mkiso.d/filemap.yml.
    '''
    this_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(this_dir, 'mkiso.d')
    filemap_fname = os.path.join(src_dir, 'filemap.yml')
    filemap = {}
    with open(filemap_fname, 'r') as f:
        filemap = yaml.load(f.read())
    for src, dest in filemap.items():
        src_fullpath = os.path.join(src_dir, src)
        dest_fullpath = os.path.join(tmp_dir, dest)
        run_cmd(['cp', src_fullpath, dest_fullpath])


def execute(args):
    tmp_dir = 'tmp/ubuntu-16-server-tmp-dir'
    unpack(args.orig_iso, tmp_dir)
    modify(tmp_dir)
    pack(tmp_dir, args.new_iso)


def main():
    XENIAL_SERVER_ISO_URL = \
        'http://mirror.steadfast.net/ubuntu-releases/16.04.2/ubuntu-16.04.2-server-amd64.iso'
    def __iso(s):
        '''
        If @s is a string that starts with
        '''
        if s.startswith('http://') \
                or s.startswith('tftp://') \
                or s.startswith('https://'):
            tmp_iso = '/tmp/ubuntu-16-server.iso'
            if os.path.isfile(tmp_iso):
                LOG.info('File %s already exists.' % tmp_iso)
                LOG.info('Skip downloading the iso from %s.' % s)
                return tmp_iso
            run_cmd(['wget', s, '--output-document', tmp_iso])
            return tmp_iso
        else:
            return s

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('new_iso',
            help='The file name of the generated iso image.')
    parser.add_argument('--orig-iso',
            metavar='URL',
            type=__iso,
            default=XENIAL_SERVER_ISO_URL,
            help='''The original ubuntu 16.04 server iso.  Could be either a URL
            or a path to a file.  Default is %s''' % XENIAL_SERVER_ISO_URL)

    args = parser.parse_args()

    execute(args)


if __name__ == '__main__':
    main()
