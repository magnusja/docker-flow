import logging

import docker
from docker.utils import LogConfig
from docker.utils.types import LogConfigTypesEnum

logger = logging.getLogger(__name__)


class DockerFlow(object):
    def __init__(self, name, tag, ports, consul_dns, logging):
        self.name = name
        self.tag = tag
        self.full_tag = name + ':' + tag
        self.logging = logging
        self.client = docker.from_env(assert_hostname=False)
        self.running_containers = self.client.containers(filters={'ancestor': name})
        logger.info('Running containers with image/name %s: %s', name, self.running_containers)

        self.host_config = self.create_host_config(ports, consul_dns, logging)

    def create_host_config(self, ports, consul_dns, logging):
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
            host_config['dns_search'] = ['service.consul']

        if logging:
            host_config['log_config'] = LogConfig(type=LogConfigTypesEnum.GELF,
                                                  config={'gelf-address': 'udp://%s:12201' % self.logging_ip})

        host_config = self.client.create_host_config(port_bindings=host_config.get('port_bindings', None),
                                                     dns=host_config.get('dns', None),
                                                     dns_search=host_config.get('dns_search', None),
                                                     log_config=host_config.get('log_config', None))

        logger.debug('host config: %s', host_config)

        return host_config

    @property
    def consul_ip(self):
        logger.info('Getting consul IP')
        consul_container = self.client.containers(filters={'name': 'consul'})

        assert len(consul_container) == 1, 'Must have exactly one consul container running'

        ip = consul_container[0]['NetworkSettings']['Networks']['bridge']['IPAddress']
        logger.info('consul IP: %s', ip)

        return ip

    @property
    def logging_ip(self):
        logger.info('Getting %s IP', self.logging)
        logging_container = self.client.containers(filters={'name': self.logging})

        assert len(logging_container) == 1, 'Must have exactly one logging container running'

        ip = logging_container[0]['NetworkSettings']['Networks']['bridge']['IPAddress']
        logger.info('logging IP: %s', ip)

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

    def pull(self):
        logger.info('Pulling docker image')
        self.check_response(self.client.pull(repository=self.name, tag=self.tag))

    def restart_container(self):
        if len(self.running_containers) > 0:
            logger.info('Stop running containers')
            for container in self.running_containers:
                logger.info('Stopping container: %s', container)
                self.client.stop(container)

        logger.info('Starting container')

        container = self.client.create_container(image=self.full_tag, host_config=self.host_config)

        self.client.start(container)


