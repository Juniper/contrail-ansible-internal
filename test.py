#!/usr/bin/python
from __future__ import print_function
import sys
import yaml
import os
import fcntl
import time
import shutil
import random
import string
import subprocess
import ConfigParser
import argparse
import glob

has_tabulate = True
try:
    from tabulate import tabulate
except:
    has_tabulate = False

LOCK_PATH = "/var/lock/contrail_ansible_test.lock"


class SingleInstance(object):
    def __init__(self):
        self.fh = None
        self.is_running = False
        try:
            self.fh = open(LOCK_PATH, 'w')
            fcntl.lockf(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except EnvironmentError as err:
            if self.fh is not None:
                self.is_running = True
            else:
                raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.fh is not None:
            fcntl.lockf(self.fh, fcntl.LOCK_UN)
            self.fh.close()
            os.unlink(LOCK_PATH)


class Prepper(object):

    def __init__(self, prepare_tasks):

        """
        Prepare test environment and cleanup them after the execution.
        """
        self.prepare_tasks = prepare_tasks
        self.dirs = []
        self.ip = []
        self.ns_name = ''.join(
            random.choice(string.ascii_lowercase + string.digits) for _ in range(10)
        )
        self.black_hole = open('/dev/null', 'wb')
        self.files = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def prepare(self):
        """
        This does bunch of tasks that is defined
        in prepare" dictionary of env.yaml
        :param prepare_tasks: dictionary of prepare tasks
        """
        method_selector = {
            "directories": self.make_dirs,
            "network": self.set_ns,
            "files": self.make_files
        }
        for action, vals in self.prepare_tasks.items():
            log('prepare', "Preparing {} => {}".format(action, vals))
            func = method_selector.get(action, lambda vals: None)
            func(vals)

    def cleanup(self):
        """
        Does cleanup job
        """
        self.cleanup_dirs()
        self.cleanup_files()
        self.cleanup_ns()

    def _mkdirp(self, directory):
        """
        Recursively create directories
        :param dir:
        :return:
        """
        if not os.path.isdir(directory):
            os.makedirs(directory)

    def make_dirs(self, dirs):
        """
        Create directories recursively
        :param dirs:
        :return:
        """
        self.dirs = dirs
        for directory in self.dirs:
            self._mkdirp(directory)
        return True

    def cleanup_dirs(self, backup=False, backup_path=None):
        """
        Cleanup the directories created by make_dirs
        :param backup: whether to backup directories before cleanup
        :param backup_path: directory path under which the backup is made
        :return: True or False
        """
        for directory in self.dirs:
            try:
                shutil.rmtree(directory)
            except OSError:
                # The directory not found which is okay
                pass

    def make_files(self, files):
        """
        Touch empty files
        :param files: list of files to be created
        :return:
        """
        self.files = files
        for file in self.files:
            basedir = os.path.dirname(file)
            if not os.path.exists(basedir):
                os.makedirs(basedir)
            open(file, 'a').close()

    def cleanup_files(self):
        for file in self.files:
            try:
                os.remove(file)
            except OSError:
                # The directory not found which is okay
                pass

    def set_ns(self, ip_data):
        """
        Create a netns with ip_addresses set
        :param ip_data: dictionary of ip details
        :return:
        """
        ip_addresses = ip_data.get('ip', [])
        gateway = ip_data.get('gateway', None)
        subprocess.call(['rmmod', 'dummy'], stderr=self.black_hole)
        subprocess.call(['modprobe', 'dummy'])
        subprocess.call(['ip', 'link', 'set', 'name', self.ns_name, 'dev', 'dummy0'])
        subprocess.call(['ip', 'netns', 'add', self.ns_name])
        subprocess.call(['ip', 'link', 'set', self.ns_name, 'netns', self.ns_name])
        for ip in ip_addresses:
            subprocess.call(['ip', 'netns', 'exec', self.ns_name,'ip', 'addr',
                             'add', ip, 'dev', self.ns_name])
        subprocess.call(['ip', 'netns', 'exec', self.ns_name, 'ip', 'link',
                         'set', self.ns_name, 'up'])
        if gateway:
            subprocess.call(['ip', 'netns', 'exec', self.ns_name, 'ip', 'route',
                             'add', 'default', 'via', gateway])
        return True

    def cleanup_ns(self):
        """
        cleanup netns created
        """
        p = subprocess.Popen(['ip','netns'], stdout=subprocess.PIPE)
        netns_list = p.communicate()[0].split('\n')
        if self.ns_name in netns_list:
            subprocess.call(['ip', 'netns', 'delete', self.ns_name])
        subprocess.call(['rmmod', 'dummy'], stderr=self.black_hole)


def run_contrailctl(component, ns_name, config_file=None):
    log("run_contrailctl", "Running contrailctl for {}".format(component))
    if config_file:
        cctl_cmd = ['ip', 'netns', 'exec', ns_name, 'contrailctl', 'config',
                    'sync', '-c', component, '-t', 'test', '-Ff', config_file]
    else:
        cctl_cmd = ['ip', 'netns', 'exec', ns_name, 'contrailctl', 'config',
                    'sync', '-c', component, '-t', 'test', '-F']
    try:
        return subprocess.call(cctl_cmd)
    except OSError as e:
        log('run_contrailctl', "Failed to find contrailctl, does it even installed?")
        return 2


def get_lock(fail=False, timeout=60):
    poll = 10
    total_wait_time = 0
    print_start = False
    while True:
        with SingleInstance() as si:
            if si.is_running:
                if fail:
                    return False
                else:
                    if total_wait_time > timeout:
                        print("Wait timeout after %s seconds" % timeout)
                        return False
                    if total_wait_time < poll:
                        if not print_start:
                            print("Waiting for already running process to finish.", end='')
                            print_start = True
                        else:
                            print('.', end='')
                    time.sleep(poll)
                    total_wait_time += poll
            else:
                return True


def parse_yaml(file):
    """ Parse yaml file and return a dictionary
    :param file: yaml file to be parsed
    """
    with open(file, 'r') as stream:
        return yaml.load(stream)


def log(owner, msg):
    """
    Log messages to console
    :param owner: A string on who write the message
    :param msg: Log message
    """
    print("{} | {}".format(owner, msg))


def read_ini_file(file):
    """
    Read ini file and return a dict
    :param file: ini file
    :return: dictionary that has the content of ini file
    """
    ini_dict = {}
    cp = ConfigParser.ConfigParser()
    cp.read(file)
    for section in cp.sections():
        ini_dict[section] = {}
        for option in cp.options(section):
            ini_dict[section][option] = cp.get(section, option)
    if cp.defaults():
        ini_dict['DEFAULT'] = cp.defaults()
    return ini_dict


def validate_ini(file, expected_config):
    if not os.path.isfile(file):
        log("Validate", "ERROR| Configuration file {} does not exist".format(file))
        return 1
    current_config = read_ini_file(file)
    failed_config = []
    print("Validating {}: ".format(file), end='')
    for section, config in expected_config.items():
        for option, expected_value in config.items():
            current_config_value = current_config.get(section, {}).get(option.lower(), None)
            if str(current_config_value).strip() == str(expected_value).strip():
                print('.', end='')
            else:
                print('f',end='')
                failed_config.append(("{}.{}".format(section, option), current_config_value, expected_value))
    print('')
    return failed_config


def print_failed_report(failed_config):
    failures_list=[]
    for file, failures in failed_config.items():
        for entry in failures:
            print (entry)
            failures_list.append([file, entry[0], entry[2], entry[1]])

    if not has_tabulate:
        print("tabulate python module is not installed, printing failed report with minimal formatting")
        print("{:>40}{:>40}{:>20}{:>20}".format('CONFIG FILE', 'CONFIGURATION', 'EXPECTED VALUE', 'CURRENT VALUE'))
        for entry in failures_list:
            print("{:>40}{:>40}{:>20}{:>20}".format(entry[0], entry[1], entry[2], entry[3]))
    else:
        print(tabulate(failures_list, headers=['CONFIG FILE', 'CONFIGURATION', 'EXPECTED VALUE', 'CURRENT VALUE']))


def validate(values):
    """
    Validate the values against configuration entries
    :param values: dictionary of configuration file and values expected.
    :return: True or false
    """
    failed_config = {}
    for file, data in values.items():
        for ftype, config_data in data.items():
            if ftype == 'ini_file':
                failures = validate_ini(file, config_data)
                if failures:
                    failed_config.update({file: failures})
    return failed_config


def worker():
    """worker function which iterate through all test scenarios found under
    `pwd`/tests directory and initiate tests
    :return: 0 when tests passed 1 when tests failed
    """
    playbook_dir = os.path.join(os.path.abspath(os.path.curdir), 'playbooks')
    if not os.path.isdir(playbook_dir):
        log("worker", "ERROR|playbook directory {} does not exist".format(playbook_dir))
    test_dir = os.path.join(os.path.abspath(os.path.curdir), 'tests')
    scenarios = [os.path.join(test_dir, name) for name in os.listdir(test_dir)
        if os.path.isdir(os.path.join(test_dir, name))]

    if not scenarios:
        log("worker", "ERROR|No scenarios found in {}".format(test_dir))

    if os.environ.get('CONTRAIL_COMPONENTS', None):
        components = os.environ['CONTRAIL_COMPONENTS'].split(',')
    else:
        components = ['controller','analytics', 'analyticsdb',
                      'kubemanager', 'mesosmanager']

    for scenario in scenarios:
        env_yaml = os.path.join(scenario, 'env.yaml')
        values_yaml = os.path.join(scenario, 'values.yaml')
        values_dir = os.path.join(scenario, 'values')
        if not os.path.isfile(env_yaml):
            log("worker", "ERROR| env.yaml does not found for scenario {}".format(scenario))
            return 1
        values_dict = {}
        if os.path.isfile(values_yaml):
            values_dict = parse_yaml(values_yaml)
        elif os.path.isdir(values_dir):
            for yml_file in glob.iglob("{}/*.yaml".format(values_dir)):
                values_dict.update(parse_yaml(yml_file))
        else:
            log("worker", "ERROR| values.yaml or values directory does not found for scenario {}".format(scenario))
            return 1

        log("worker", "Testing the scenario {}".format(scenario))
        env_dict = parse_yaml(env_yaml)
        with Prepper(env_dict.get('prepare', {})) as prep:
            prep.prepare()
            log("worker", "Running contrailctl")
            os.environ['PLAYBOOK_DIRECTORY'] = playbook_dir
            for component in components:
                config_file = os.path.join(test_dir, scenario, component + '.conf')
                if os.path.isfile(config_file):
                    cfg = config_file
                else:
                    cfg = None
                rv = run_contrailctl(component, prep.ns_name, cfg)
                if rv != 0:
                    log("worker", "contrailctl run failed")
                    return 1
            log("worker", "Running tests ")
            failures = validate(values_dict)
            if failures:
                log("worker", "Finished tests with failures")
                print_failed_report(failures)
            else:
                log("worker", "Finished tests successfully")
    return 0


def main(args=sys.argv[1:]):
    lock = get_lock(True)
    if not lock:
        return 1
    else:
        return worker()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
