[![Build Status](https://travis-ci.org/adsabs/mission-control.svg?branch=master)](https://travis-ci.org/adsabs/mission-control)
[![Coverage Status](https://coveralls.io/repos/adsabs/mission-control/badge.svg?branch=master&service=github)](https://coveralls.io/github/adsabs/mission-control?branch=master)

# Mission-control

Build and CI platform for adsabs.
  * Builds docker images based on templates. Triggered by github webhooks
  * Pushes successfully build images to dockerhub with the commit hash as tag
 
# Development

You can run unit tests in the following way:
```bash
nosetests mc/tests/unittests
```

A Vagrantfile and puppet manifest are available for development within a virtual machine. To use the vagrant VM defined here you will need to install *Vagrant* and *VirtualBox*. 

  * [Vagrant](https://docs.vagrantup.com)
  * [VirtualBox](https://www.virtualbox.org)

To load and enter the VM: `vagrant up && vagrant ssh`

# Manage.py deploy workflow:

  1. The image should have been built and pushed to dockerhub. If the docker image is for whatever reason inaccessible, the deployment (last step) will fail. One can manually build commits via

      `python mc/manage.py dockerbuild --repo $REPO --commit $HASH`
  
  1. Print the JSON task definition:
      
      `json=$(python mc/manage.py print_task_def --containers metrics_service:a07fc3bf3e1307fff7ac31f7aba85a8576395128 staging 300 --family metrics_service)`

      (300: Megabytes to allocate to the container. This is the criterion ECS uses to allocate services amongst the cluster, so it should be well-understood)
      
  1. Register the JSON task definition the AWS-ECS:

      `python mc/manage.py register_task_def --task "$json"`

  1. Update the running ECS service with the newly updated task definition:

      `python mc/manage.py update_service --cluster staging --service metrics_service --desiredCount 1 --taskDefinition metrics_service`
      
