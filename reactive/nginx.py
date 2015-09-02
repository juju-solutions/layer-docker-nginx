import os
import shutil

from subprocess import check_call

from charmhelpers.core import hookenv

from charms import reactive
from charms.reactive import hook
from charms.reactive import when
from charms.reactive import when_not


@hook('config-changed')
def config_changed():
    config = hookenv.config()
    if config.changed('port'):
        stop_container()
        reactive.set_state('nginx.start')


@when('docker.available')
@when_not('nginx.start', 'nginx.started', 'nginx.stopped')
def install_nginx():
    copy_assets()
    hookenv.status_set('maintenance', 'Pulling Nginx image')
    check_call(['docker', 'pull', 'nginx'])
    reactive.set_state('nginx.start')


@when('nginx.start', 'docker.available')
@when_not('nginx.started')
def run_container():
    config = hookenv.config()

    # Run the nginx docker container.
    run_command = [
        'docker',
        'run',
        '--restart',
        'on-failure',
        '--name',
        'docker-nginx',
        '-v',
        '/srv/docker-nginx:/usr/share/nginx/html:ro',
        '-p',
        '{}:80'.format(config['port']),
        '-d',
        'nginx'
    ]
    check_call(run_command)
    hookenv.open_port(config['port'])
    reactive.remove_state('nginx.stopped')
    reactive.remove_state('nginx.start')
    reactive.set_state('nginx.started')
    hookenv.status_set('active', 'Nginx container started')


@when('nginx.stop', 'docker.available')
@when_not('nginx.stopped')
def stop_container():
    hookenv.status_set('maintenance', 'Stopping Nginx container')
    # make this cleaner
    try:
        check_call(['docker', 'kill', 'docker-nginx'])
    except:
        pass
    try:
        check_call(['docker', 'remove', 'docker-nginx'])
    except:
        pass
    reactive.remove_state('nginx.started')
    reactive.remove_state('nginx.stop')
    reactive.set_state('nginx.stopped')


@when('nginx.started', 'website.available')
def configure_website_port(http):
    config = hookenv.config()
    serve_port = config['port']
    http.configure(port=serve_port)
    hookenv.status_set('active', '')


def copy_assets():
    hookenv.status_set('maintenance', 'Copying charm assets in place')
    charm_path = os.environ.get('CHARM_DIR')
    if not os.path.exists('/srv/docker-nginx'):
        os.path.mkdir('/srv/docker-nginx')
        shutil.copyfile(os.path.join(charm_path, 'assets/index.html'),
                        '/srv/docker-nginx/index.html')
        shutil.copyfile(os.path.join(charm_path, 'assets/jujuanddocker.png'),
                        '/srv/docker-nginx/jujuanddocker.png')
