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
        logger.debug([line for line in generator])

    def build(self):
        self.check_response(self.client.build('./', tag=self.full_tag))

    def restart_container(self):
        if len(self.running_containers) > 0:
            logger.info('Stop running containers')
            for container in self.running_containers:
                logger.info('Stopping container: %s', container)
                self.client.stop(container)

        logger.info('Starting container')
        container = self.client.create_container(image=self.full_tag)
        self.client.start(container)


