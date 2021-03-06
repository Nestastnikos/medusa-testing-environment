# -*- coding: utf-8 -*-
"""@package mte.tpm
Prepares new thread for starting the virtual machine
"""
import threading
import virtual


def main(test_list, suite_list):
    """
    Creates a new thread for module used to communicate with VirtualBox
    @param test_list: This list contains names of system calls to be tested.
    @param suite_list: This list contains names of the testing suites to be run.
    Names of tests and suites that can be chosen are listed in the config module.
    @return: None
    """
    thread = threading.Thread(target=virtual.main, args=(test_list, suite_list), name='vbox')
    thread.start()


def setup_virtual_pc():
    """
    Used when installing the testing environment to a virtual computer.
    """
    thread = threading.Thread(target=virtual.setup_virtual_pc(), name='vbox')
    thread.start()

if __name__ == '__main__':
    main(['fork', 'mkdir', 'symlink', 'mknod', 'rmdir', 'unlink'], ['do_tests'])
    # main(sys.argv)
