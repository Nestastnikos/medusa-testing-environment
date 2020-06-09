"""
@package mits.testing
This module executes tests and testing suites
"""
import os
import pickle
import time
import sys
import tabulate
import commons
import test_registrator as TestRegistrator
from asynchronous_reader import Reader
from logger import log_guest
import path_injector as PathInjector


def test_director(pickle_location):
    """
    Unpickles tuple of tests and suites chosen by the user to be executed.
    Based on the selected tests, it creates configuration for Constable.
    @param pickle_location: File name of the pickled test information
    """
    def unpickle_tests(tests_path):
        """
        Reads pickled tests from test_path, which were pickled by host system.
        @param tests_path: Full path to the pickled data file.
        @return: Pickled data. It should be tuple of lists containing names of
        the tests and suites, respectively.
        """
        with open(tests_path, 'rb') as f:
            return pickle.load(f, fix_imports=True)

    os.chdir(commons.TESTING_PATH)
    TestRegistrator.register_suites()

    pickle_tests_path = os.path.join(commons.VM_MTE_PATH, pickle_location)
    execution_category = unpickle_tests(pickle_tests_path)
    print(execution_category)
    log_guest(f"Test category to be run is {execution_category}")

    suites_to_run = TestRegistrator.get_test_suites_for(execution_category)

    make_authserver_config()
    for test_category, test_suites in suites_to_run.items():
        make_final_config(test_category, test_suites)
        (results, outputs, outputs_denied) = start_suite(test_suites)
        print_class_report(results)


def start_suite(suites):
    """
    Main testing function, starts Constable and executes suites one after the
    other. When all testing is done, results are sent to the validator module
    to be validated.
    @param suites: List of system calls to be tested and called
    @return: Tuple of results and outputs. Outputs list is included only in
    concurrent suite, otherwise it's None.
    """
    def get_setup_and_cleanup_routines(suites):
        suite_cleanups = []
        suite_setups = []
        for suite in suites:
            suite_cleanups.append(suite._suite_cleanup)
            suite_setups.append(suite._suite_setup)
        return (suite_setups, suite_cleanups)

    def setup_environment(suite_setups):
        log_guest('Setup of environment for test execution')
        for suite_setup in suite_setups:
            suite_setup()

    def execute_suites(suites):
        log_guest('Starting Constable')
        constable = Reader('sudo constable ' + commons.TESTING_PATH + '/constable.conf')
        # Catch first outputs and save them independently to testing outputs

        time.sleep(1)
        log_guest('Starting test batch')
        results = class_tests(suites)

        log_guest('Terminating Constable')
        constable.terminate()
        return results

    def cleanup_environment(suite_cleanups):
        log_guest('Cleanup of environment after testing')
        for suite_cleanup in suite_cleanups:
            suite_cleanup()

    (suite_setups, suite_cleanups) = get_setup_and_cleanup_routines(suites)

    setup_environment(suite_setups)
    results = execute_suites(suites)
    cleanup_environment(suite_cleanups)

    return (results, None, None)


def make_authserver_config():
    log_guest('Creating configuration for authserver /constable.conf')
    old_config_path = f'{commons.VM_MTE_PATH}/constable.conf'
    new_config_path = f'{commons.TESTING_PATH}/constable.conf'
    with open(new_config_path, 'w') as config_out:
        with open(old_config_path, "r") as config_file:
            config_content = config_file.read()
            config_content = PathInjector.inject_paths(config_content)
            config_out.write(config_content)


def make_final_config(test_category, test_suites):
    """
    Creates configuration file based on chosen testing classes.
    @param tests: List of test classes from which tests should be executed
    during testing.
    """
    def get_required_configs():
        config_filenames = [f'{commons.VM_MTE_PATH}/{test_category}.conf']
        print(config_filenames)
        for test_suite in test_suites:
            filename = test_suite.__class__.__name__.lower()
            config_filenames.append(f'{commons.VM_MTE_PATH}/{filename}.conf')
            log_guest(f"Config {filename} appended to list")

        return config_filenames

    log_guest(f'Creating configuration /medusa.conf for {test_category}')
    config_filenames = get_required_configs()
    with open(f'{commons.TESTING_PATH}/medusa.conf', 'w') as config_out:
        for config_filename in config_filenames:
            with open(config_filename, "r") as config_file:
                config_content = config_file.read()
                config_content = PathInjector.inject_paths(config_content)
                config_out.write(config_content)


def class_tests(test_classes):
    results = {}
    for test_class in test_classes:
        tests = test_class.tests
        for test_name, test_case in tests:
            log_guest(f'Executing test {test_name}: {test_case}')
            results[test_name] = str(test_case())

    return results


def print_class_report(results):
    headers = ['Test name', 'Is passed']
    rows = [(name, result) for name, result in results.items()]
    print(tabulate.tabulate(rows, headers=headers))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
    test_director(sys.argv[1])