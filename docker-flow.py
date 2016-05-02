import argparse
import logging

import dockerflow

logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(level=logging.CRITICAL, format='%(message)s')
    logger = logging.getLogger(dockerflow.__name__)
    logger.setLevel(logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)


def setup_argparser():
    parser = argparse.ArgumentParser(description='Docker CI/CD workflow.')
    parser.add_argument('--name', type=str, help='Docker image/container name', required=True)
    parser.add_argument('--tag', type=str, help='Image tag', default='latest')
    parser.add_argument('--build', help='Build image from ./Dockerfile', action='store_true')
    parser.add_argument('--push', help='Push image to registry or docker hub', action='store_true')

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

    flow.restart_container()


if __name__ == '__main__':
    main()
