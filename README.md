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
