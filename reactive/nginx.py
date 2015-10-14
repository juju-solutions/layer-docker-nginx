import os
import shutil

from subprocess import check_call

from charmhelpers.core import hookenv
from charmhelpers.core import unitdata
from charmhelpers.fetch import install_remote

from charms import reactive
from charms.reactive import hook
from charms.reactive import when
from charms.reactive import when_not

db = unitdata.kv()
config = hookenv.config()


@hook('config-changed')
def config_changed():
    '''
    On every config changed hook execution, check for port changes - if the
    port has changed, we need to force stop the container and re-execute.
    Otherwise, check repo/webroot and handle accordingly under the clone
    directive.
    '''
    if config.changed('port'):
        stop_container()
    clone_repository()


@when('docker.available')
def install_nginx():
    '''
    Default to only pulling the image once. A forced upgrade of the image is
    planned later. Updating on every run may not be desireable as it can leave
    the service in an inconsistent state.
    '''
    if reactive.is_state('nginx.available'):
        return
    copy_assets()
    hookenv.status_set('maintenance', 'Pulling Nginx image')
    check_call(['docker', 'pull', 'nginx'])
    reactive.set_state('nginx.available')


@when('nginx.available', 'docker.available')
@when_not('nginx.started')
def run_container(webroot=None):
    '''
    Wrapper method to launch a docker container under the direction of Juju,
    and provide feedback/notifications to the end user.
    '''
    if not webroot:
        webroot = config.get('webroot')
    # Run the nginx docker container.
    run_command = [
        'docker',
        'run',
        '--restart',
        'on-failure',
        '--name',
        'docker-nginx',
        '-v',
        '{}:/usr/share/nginx/html:ro'.format(webroot),
        '-p',
        '{}:80'.format(config.get('port')),
        '-d',
        'nginx'
    ]
    check_call(run_command)
    hookenv.open_port(config.get('port'))
    reactive.remove_state('nginx.stopped')
    reactive.set_state('nginx.started')
    hookenv.status_set('active', 'Nginx container started')


@when('nginx.stop', 'docker.available')
@when_not('nginx.stopped')
def stop_container():
    '''
    Stop the NGinx application container, remove it, and prepare for launching
    of another application container so long as all the config values are 
    appropriately set.
    '''
    hookenv.status_set('maintenance', 'Stopping Nginx container')
    # make this cleaner
    try:
        check_call(['docker', 'kill', 'docker-nginx'])
    except:
        pass
    try:
        check_call(['docker', 'rm', 'docker-nginx'])
    except:
        pass
    reactive.remove_state('nginx.started')
    reactive.remove_state('nginx.stop')
    reactive.set_state('nginx.stopped')
    hookenv.status_set('waiting', 'Nginx container stopped')


@when('nginx.started', 'website.available')
def configure_website_port(http):
    '''
    Relationship context, used in tandem with the http relation stub to provide
    an ip address (default to private-address) and set the port for the
    relationship data
    '''
    serve_port = config.get('port')
    http.configure(port=serve_port)
    hookenv.status_set('active', '')


def copy_assets():
    '''
    First time setup. Give the user a simple HTML site to validate they
    are indeed running nginx, in a Docker container, under the direction of
    Juju.
    '''
    hookenv.status_set('maintenance', 'Copying charm assets in place')
    charm_path = os.environ.get('CHARM_DIR')
    if not os.path.exists('/srv/docker-nginx'):
        os.makedirs('/srv/docker-nginx')
        shutil.copyfile(os.path.join(charm_path, 'assets/index.html'),
                        '/srv/docker-nginx/index.html')
        shutil.copyfile(os.path.join(charm_path, 'assets/jujuanddocker.png'),
                        '/srv/docker-nginx/jujuanddocker.png')


def clone_repository(branch='master'):
    '''
    Wrapper method around charmhelpers.install_remote to handle fetching of a
    vcs url to deploy a static website for use in the NGinx container.
    '''
    repo_dir = None

    if config.get('repository'):
        hookenv.status_set('maintenance', 'Cloning repository')

        if not config.changed('repository'):
            repo_dir = db.get('repo_dir')

        repo_dir = install_remote(config.get('repository'), dest=config.get('webroot'),
                                  branch=branch, depth=None)
        db.set('repo_dir', repo_dir)
        stop_container()
        run_container(repo_dir)
        hookenv.status_set('active', '')


