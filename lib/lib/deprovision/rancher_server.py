#!/usr/bin/env python3
# coding: us-ascii
# mode: python

import sys, logging, os, colorama
from invoke import run, Failure
from colorama import Fore
from pprint import pprint as pp

colorama.init()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
stream = logging.StreamHandler()
stream.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s - %(message)s'))
log.addHandler(stream)

DOCKER_MACHINE = "docker-machine --storage-path /workdir/.docker/machine "


#
def log_err(msg):
     log.error(Fore.RED + str(msg) + Fore.RESET)


#
def err_and_exit(msg, code=-1):
     log_err(msg)
     sys.exit(-1)


#
def missing_envvars(envvars=['AWS_PREFIX', 'RANCHER_SERVER_OPERATINGSYSTEM']):
     missing = []
     for envvar in envvars:
          if envvar not in os.environ:
               missing.append(envvar)
     log.debug("Missing envvars: {}".format(missing))
     return missing


#
def deprovision_rancher_server():

     aws_prefix = os.environ.get('AWS_PREFIX')

     machine_name = "{}-vtest-server0".format(os.environ['RANCHER_SERVER_OPERATINGSYSTEM'])
     if aws_prefix:
          machine_name = "{}-".format(aws_prefix) + machine_name

     try:
          cmd = DOCKER_MACHINE + "rm -y {}".format(machine_name)
          run(cmd, echo=True)

     except Failure as e:
          if 'RANCHER_SERVER_MISSING_OK' in os.environ and 'Host does not exist' in e.result.stderr:
               log.debug("Did not find a node for hosting rancher/server at \'{}\'...assuming that is ok.".format(machine_name))
          else:
               log.error("Failed while deprovisioning Rancher Agents!: {} :: {}".format(e.result.return_code, e.result.stderr))
               return False

     return True


#
def main():
     if os.environ.get('DEBUG'):
          log.setLevel(logging.DEBUG)
          log.debug("Environment:")
          log.debug(pp(os.environ.copy(), indent=2, width=1))

     # validate our envvars are in place
     missing = missing_envvars()
     if [] != missing:
          err_and_exit("Unable to find required environment variables! : {}".format(', '.join(missing)))

     if not deprovision_rancher_server():
          err_and_exit("Failed while deprovisioning rancher/server!")


if '__main__' == __name__:
    main()