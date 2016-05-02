import logging

import docker

logger = logging.getLogger(__name__)


class DockerFlow(object):
    def __init__(self, name, tag):
        self.name = name
        self.tag = tag
        self.full_tag = name + ':' + tag
        self.client = docker.from_env(assert_hostname=False)
        self.running_containers = self.client.containers(filters={'ancestor': name})
        logger.info('Running containers with image/name %s: %s', name, self.running_containers)

    @property
    def consul_ip(self):
        logger.info('Getting consul IP')
        consul_container = self.client.containers(filters={'name': 'consul'})

        assert len(consul_container) == 1, 'Must have exactly one consul container running'

        ip = consul_container[0]['NetworkSettings']['Networks']['bridge']['IPAddress']
        logger.info('consul IP: %s', ip)

        return ip

    def check_response(self, generator):
        result = ''
        for line in generator:
            result += line
        logger.debug(result)

    def build(self):
        logger.info('Building docker image')
        self.check_response(self.client.build('./', tag=self.full_tag))

    def push(self):
        logger.info('Pushing docker image')
        self.check_response(self.client.push(repository=self.name, tag=self.tag))

    def restart_container(self, consul_dns, ports=None):
        if len(self.running_containers) > 0:
            logger.info('Stop running containers')
            for container in self.running_containers:
                logger.info('Stopping container: %s', container)
                self.client.stop(container)

        logger.info('Starting container')

        host_config = dict()
        if ports:
            port_map = dict()
            for port in ports:
                host_ip, container_port = port.rsplit(':', 1)
                if ':' in host_ip:
                    host_ip = tuple(host_ip.split(':'))

                port_map[container_port] = host_ip

            host_config['port_bindings'] = port_map

        if consul_dns:
            host_config['dns'] = [self.consul_ip, '8.8.8.8']

        host_config = self.client.create_host_config(port_bindings=host_config.get('port_bindings', None),
                                                     dns=host_config.get('dns', None))

        logger.debug('host config: %s', host_config)

        container = self.client.create_container(image=self.full_tag)

        self.client.start(container, dns_search=['service.consul'] if consul_dns else None,
                          port_bindings=host_config.get('PortBindings', None),
                          dns=host_config.get('Dns', None))


