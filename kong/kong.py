import json
import logging

import requests

logger = logging.getLogger(__name__)


class KongApiGateway(object):
    def __init__(self, host):
        self.host = host

    def register_api(self, name, payload):
        url = self.host + '/apis/'

        logger.info('Deleting API with name %s', name)
        response = requests.delete(url + name)
        logger.debug(response.status_code)
        logger.debug(response.text)

        logger.info('Adding API with name %s', name)
        response = requests.post(url, json=payload)
        logger.debug(response.text)
        assert response.status_code == 201, 'Kong API adding error'

    def add_plugin(self, name, plugin):
        url = self.host + '/apis/' + name + '/plugins'
        logger.info('Adding plugin to API with name %s', name)
        response = requests.post(url, json=plugin)
        logger.debug(response.text)
        assert response.status_code == 201, 'Kong API adding error'


def configure_kong(host, kong_json, plugins=None):
    name = kong_json['name']
    kong = KongApiGateway(host)
    kong.register_api(name, kong_json)

    if plugins:
        for plugin in plugins:
            with open(plugin) as p:
                kong.add_plugin(name=name, plugin=json.load(p))
