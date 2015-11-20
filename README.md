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
nosetests mc/tests/livetests (this will create/run real containers)
```

A Vagrantfile and puppet manifest are available for development within a virtual machine. To use the vagrant VM defined here you will need to install *Vagrant* and *VirtualBox*. 

  * [Vagrant](https://docs.vagrantup.com)
  * [VirtualBox](https://www.virtualbox.org)

To load and enter the VM: `vagrant up && vagrant ssh`

# Adding services

To add a service to mission-control for a specific feature, you will need to follow the instructions below:

  * Automatic builds to Docker registry on GitHub commit:
    1. Add the service to the "**WATCHED_REPOS**" list in `mc/config.py`
    2. Update and restart the mission_control web service

  * CI Testing
    1. You will need to include stub data for the relevant dependencies that the tests will use:
      1. Solr
      2. Postgres
      3. Consul
    2. Update the `config/adsws/staging/WEBSERVICES` in the Consul key-value store `mc/templates/consul/adsws/adsws.config.json` for service discovery.
    3. Check it is in the KNOWN_SERVICES in the Postgres provisioner (this should be removed soon).

# Manage.py

## CI Testing workflow on-premises:

  1. Check the YAML file has the correct configuration for what you want to test against:
     ```yml
     dependencies:
       - name: redis
         image: redis:2.8.21
     services:
       - name: graphics_service
         repository: adsabs
         tag: dd905b927323e1ecf2a563a80d2bc5d9d98b62b4
     ```

     This example will start redis using the 2.8.21 image, and the graphics service for the relevant commit hash. The following keywords are available:
       * dependencies: this is a stand alone service that our infrastructure relies on, possible values: redis, postgres, solr, consul, registrator
         * name: name of the service
         * image: docker image to use (docker convention is used)
         * requirements: which containers does the service need to know exist
         * build_requirements: which containers does the service need to know exist *ON BUILD*
       * services: this is our application tier, and so any service that is part of our microservice layer, possible values: graphics_service, metrics_service, recommender_service, solr-service, export_service, myads, orcid-service, citation_helper_service, vis-services, biblib-service, adsws
         * name: name of the service
         * repository: Docker registry repository it belongs to
         * tag: commit hash/tag of the container
       * tests: this refers to what functional tests to run on the test cluster, possible values: adsrex

  2. Run the tests
    ```bash
    python mc/manage.py test_cluster -c run
    ```
  3. Check the results
    ```bash
    cat .mc.ci
    ```

  **Note**: The YAML list is order dependent, much like in the TravisCI .travis.yml file.

## Deploy a service workflow in ECS:

  1. The image should have been built and pushed to dockerhub. If the docker image is for whatever reason inaccessible, the deployment (last step) will fail. One can manually build commits via

      ```bash
      python mc/manage.py dockerbuild --repo $REPO --commit $HASH
      ```

  1. Print the JSON task definition:

      ```bash
      json=$(python mc/manage.py print_task_def --containers metrics_service:a07fc3bf3e1307fff7ac31f7aba85a8576395128 staging 300 --family metrics_service)
      ```

      (300: Megabytes to allocate to the container. This is the criterion ECS uses to allocate services amongst the cluster, so it should be well-understood)

  1. Register the JSON task definition the AWS-ECS:

      ```bash
      python mc/manage.py register_task_def --task "$json"
      ```

  1. Update the running ECS service with the newly updated task definition:

      ```bash
      python mc/manage.py update_service --cluster staging --service metrics_service --desiredCount 1 --taskDefinition metrics_service
      ```

## Deploy a task workflow in ECS

 * Consul back-up
