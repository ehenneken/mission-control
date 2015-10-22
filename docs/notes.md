#

## API

Each service that runs a container must contain the following parameters:
  * CONSUL_HOST: the dns/ip of the consul cluster.
  * CONSUL_PORT: the port of the consul cluster.
  * ENVIRONMENT: the environment that is being run, specifically 'staging' or 'production'.
  * SERVICE: the name of the service itself, eg., 'adsws'. This corresponds to the naming used in the key/value store of consul.

Currently, these are set in the GunicornDockerRunner, and the generic DockerRunner service on instantiation.


ADSWS Settings

NUM_PROXIES: 
  * Int: 0, 1, 2, N
  * The number of proxies that sit infront of the ADSWS. Within the cloud this is 2, because there is the elastic load balancer, and then nginx within the docker container. When running locally within a container, it is 1, as you only have nginx. When running wsgi directly, this can be set to 0. This number is only important when the flag 'PRODUCTION' is set to True, otherwise it is not executed. When running wsgi directly, and not loading a consul config, this will not be an issue.

PRODUCTION: 
  * True/False
  * Tells the application factory that there are proxies in the way of the application, and this must be handlded correctly. The configuration for the proxies is defined by NUM_PROXIES.

OAUTH2_CLIENT_SECRET_SALT_LEN:
  * This value must be positive and non-zero

BOOTSTRAP_USER_EMAIL:
  * string
  * If the user is not logged in, the requesting user is set to be the anonymous user: 'anonymous@ads'
