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

    def check_response(self, generator):
        result = ''
        for line in generator:
            result += line
        logger.debug(result)

    def build(self):
        logger.info('Building docker image')
        self.check_response(self.client.build('./', tag=self.full_tag))

    def push(self):
        logger.info('Pushing docker image to')
        self.check_response(self.client.push(repository=self.name, tag=self.tag))

    def restart_container(self):
        if len(self.running_containers) > 0:
            logger.info('Stop running containers')
            for container in self.running_containers:
                logger.info('Stopping container: %s', container)
                self.client.stop(container)

        logger.info('Starting container')
        container = self.client.create_container(image=self.full_tag)
        self.client.start(container)


