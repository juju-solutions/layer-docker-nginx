# Charm Layer NGinx

This layer works in tandem with the `docker` layer to deliver NGinx in an
application container. This charm is pretty basic for the purpose of education
when charming with docker in a classical example of delivering a simple webapp.

### Usage

This charm relies on `charm compose` which is provided by the `charm-tools`
package.

    add-apt-repository ppa:juju/stable
    apt-get install charm-tools

Once you have Charm Tools installed, you can build this charm from scratch by
running:

    charm compose -o $CHARM_REPOSITORY -l DEBUG

This will create a `trusty/docker-nginx` charm in your `$CHARM_REPOSITORY`
ready to deploy to your environment like so:

    juju deploy local:trusty/docker-nginx
    juju expose docker-nginx

Once the docker-nginx service has completed setup, and the service is exposed
it is reachable via the public-ip of the service http://docker-nginx-public-ip

To deploy a static HTML site out of VCS (BZR and Git are currently supported)
set the repository path on the charm to a public clone url of your project:

    juju set docker-nginx repository="https://github.com/chuckbutler/Skeleton.git"

Refresh the page and you will be greeted with your freshly deployed HTML site,
served from an NGinx process running in an application container.

### Hacking

The requisit layer [docker](https://github.com/juju-solutions/layer-docker) and
this NGinx layer both leverage the reactive charming framework, and raise events
for you to consume, and use in your layers. This charm was written with the
intention of being consumed and derived for your own workloads.

#### Events

#### Subscribe-able events

> Events are emitted to notify inhereted layers that an action can
be taken. Such as the webservice coming online / offline respectively.

**nginx.started** - Emitted when the NGinx application contanier has been
launched, and is listening for connections on the configured port.

**nginx.stopped** - Emitted when the NGinx application container has been
stopped, and the configured port has been closed.


**website.available** - Emitted when the `website` relation has been configured,
this is typically used in scenarios such as relating this application to a load
balancer like [HAProxy](https://jujucharms.com/trusty/haproxy/)

#### Internal Events

> Internal events should not be subscribed/derived in additional layers, as
there is no gaurantee that your method will run before the requisit cleanup
action has been run.

**nginx.available** - Emitted when the docker image for `nginx:latest` has been
pulled, and the webserver is ready to launch.

**nginx.stop** - Emitted to halt the container, and remove the running app-container
instance and close the port.


