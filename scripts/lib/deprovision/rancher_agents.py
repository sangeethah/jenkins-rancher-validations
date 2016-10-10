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

DOCKER_MACHINE = 'docker-machine --storage-path /workdir/.docker/machine '


#
def docker_machine_status(name):
     cmd = DOCKER_MACHINE + "status {}".format(name)

     try:
          result = run(cmd, echo=True)
          log.debug("result: {}".format(result))
          if 'Stopped' in result.stdout:
               return 'Stopped'
          if 'Running' in result.stdout:
               return 'Running'

     except Failure as e:
          if 'Host does not exist' in e.result.stderr:
               return 'DNE'
          else:
               err_and_exit("Invalid docker-machine machine state. Should never get here!")


#
def log_err(msg):
     log.error(Fore.RED + str(msg) + Fore.RESET)


#
def err_and_exit(msg, code=-1):
     log_err(msg)
     sys.exit(-1)


#
def missing_envvars(envvars=['AWS_PREFIX', 'RANCHER_AGENT_OPERATINGSYSTEM']):
     missing = []
     for envvar in envvars:
          if envvar not in os.environ:
               missing.append(envvar)
     log.debug("Missing envvars: {}".format(missing))
     return missing


#
def deprovision_rancher_agents():
     aws_prefix = os.environ.get('AWS_PREFIX')
     machine_name = "{}-validation-tests-server0".format(os.environ.get('RANCHER_AGENT_OPERATINGSYSTEM'))
     if aws_prefix:
          machine_name = "{}-".format(aws_prefix) + machine_name

     try:
          server_address = run(DOCKER_MACHINE + " ip {}".format(machine_name), echo=True).stdout.rstrip()
          os.environ['RANCHER_URL'] = "http://{}:8080/v1/schemas".format(server_address)

          if 'stopped' == docker_machine_status(machine_name):
               log.info("rancher/server host node \'{}\' detected as present but 'stopped'. Skipping Agent deprovisioning. "
                        "This may require manual cleanup.".format(machine_name))

          else:
               cmd = "for i in `rancher host ls -q`; do rancher --wait rm -s $i; done"
               run(cmd, echo=True)

     except Failure as e:
          if 'RANCHER_SERVER_MISSING_OK' in os.environ and 'Host does not exist' in e.result.stderr:
               log.debug("Did not find a node for hosting rancher/server at \'{}\'...assuming that is ok.".format(machine_name))
          else:
               log.error("Failed while deprovisioning Rancher Agents!: {} :: {}".format(e.result.return_code, e.result.stderr))
               log.error("Not going to let that stop us! 'Damn the torpedos!'")

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

     if not deprovision_rancher_agents():
          err_and_exit("Failed while deprovisioning Rancher Agents!")


if '__main__' == __name__:
    main()
