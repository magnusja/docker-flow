import json
import logging
from string import Template

import docker

logger = logging.getLogger(__name__)


class LazyString(object):
    def __init__(self, callable):
        self.callable = callable

    def __str__(self):
        return self.callable()


class DockerFlow(object):
    def __init__(self, name, tag, host_config):
        self.name = name
        self.tag = tag
        self.full_tag = name + ':' + tag
        self.logging = logging
        self.client = docker.from_env(assert_hostname=False)
        self.running_containers = self.client.containers(filters={'ancestor': name})
        logger.info('Running containers with image/name %s: %s', name, self.running_containers)

        self.host_config = self.create_host_config(config=host_config) if host_config else None

    def container_ip(self, name):
        logger.info('Getting %s IP', name)
        container = self.client.containers(filters={'name': name})

        assert len(container) == 1, 'Must have exactly one %s container running' % name

        ip = container[0]['NetworkSettings']['Networks']['bridge']['IPAddress']
        logger.info('IP: %s', ip)

        return ip

    def create_host_config(self, config):
        logger.debug('host config: %s', config)
        template = Template(config)
        config = template.substitute(ip_consul=LazyString(lambda: self.container_ip('consul')),
                                     ip_logstash=LazyString(lambda: self.container_ip('logstash')))

        logger.debug('host config: %s', config)
        return json.loads(config)

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


