#!/usr/bin/env python3

import argparse
import jinja2
import logging
import os
import subprocess
import sys
import traceback


logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)


def run_cmd(cmd):
    LOG.debug(subprocess.list2cmdline(cmd))
    subprocess.check_call(cmd)


def execute(args):
    domain_name = 'xenial-try-iso'
    this_dir = os.path.dirname(os.path.abspath(__file__))
    xml_template_fname = os.path.join(this_dir, 'try_iso.d', 'bootstrap.xml.j2')
    rootfs_filename = os.path.join(this_dir, 'tmp', 'ubuntu-16-server-try-iso.img')
    iso_fname = os.path.abspath(args.iso)

    # Tweak file permissions.
    run_cmd(['chmod', '666', iso_fname])
    run_cmd(['qemu-img', 'create', '-f', 'raw', rootfs_filename, '8G'])
    run_cmd(['chmod', '666', rootfs_filename])

    # Generate xml file content.
    with open(xml_template_fname, 'r') as f:
        data = jinja2.Template(f.read()).render({
            'rootfs_filename': rootfs_filename,
            'domain_name': domain_name,
            'iso_filename': iso_fname,
        })

    # Write to xml file.
    xml_fname = 'tmp/ubuntu-16-server-try-iso.xml'
    with open(xml_fname, 'w') as f:
        f.write(data)

    # Define in libvirt and start.
    run_cmd(['virsh', 'define', xml_fname])
    try:
        run_cmd(['virsh', 'start', domain_name])
    except subprocess.CalledProcessError as e:
        traceback.print_exc()
        LOG.error(textwrap.dedent('''\
                                    ==== DO NOT PANIC ====
                Failed to start the libvirt domain.  If the error is denied file
                permission, please add the following line to
                /etc/libvirt/qemu.conf
                    dynamic_ownership = 0,
                Then restart the libvirt-bin service:
                    sudo service libvirt-bin restart

                On Ubuntu 14.04, you will also need to turn off apparmor as well
                by adding the following line to /etc/libvirt/qemu.conf:
                    security_driver = "none"
                '''))

    # Open virt-viewer to get a visual.
    run_cmd(['virt-viewer', domain_name])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso',
            help='The file name of the iso image to try.')

    args = parser.parse_args()

    execute(args)


if __name__ == '__main__':
    main()
