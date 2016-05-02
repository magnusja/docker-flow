import argparse
import json
import logging

import dockerflow
import kong

logger = logging.getLogger(__name__)


def setup_logging():
    logging.basicConfig(level=logging.CRITICAL, format='%(message)s')
    logger = logging.getLogger(dockerflow.__name__)
    logger.setLevel(logging.DEBUG)

    logger = logging.getLogger(kong.__name__)
    logger.setLevel(logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)


def setup_argparser():
    parser = argparse.ArgumentParser(description='Docker CI/CD workflow.')
    parser.add_argument('--name', type=str, help='Docker image/container name', required=True)
    parser.add_argument('--tag', type=str, help='Image tag', default='latest')
    parser.add_argument('--build', help='Build image from ./Dockerfile', action='store_true')
    parser.add_argument('--push', help='Push image to registry or docker hub', action='store_true')
    parser.add_argument('--consul-dns', help='Set DNS to container with name consul', action='store_true',
                        dest='consul_dns')
    parser.add_argument('--kong', help='Kong admin API, e.g. http://localhost:8001')
    parser.add_argument('--kong-json', help='kong.json file for registering at kong API gateway', default='kong.json')
    parser.add_argument('--kong-plugin', help='json file to activate a plugin', action='append')

    return parser


def main():
    setup_logging()

    parser = setup_argparser()
    args = parser.parse_args()

    flow = dockerflow.DockerFlow(name=args.name, tag=args.tag)

    if args.build:
        flow.build()

        if args.push:
            flow.push()

    flow.restart_container(args.consul_dns)

    if args.kong:
        with open(args.kong_json) as kong_json:
            kong.configure_kong(args.kong, kong_json=json.load(kong_json), plugins=args.kong_plugin)


if __name__ == '__main__':
    main()