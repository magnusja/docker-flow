from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='docker-flow',

    version='0.0.1',

    description='A sample Python project',

    url='https://github.com/mjdev/docker-flow',

    author='mjahnen',
    author_email='jahnen@in.tum.de',

    license='Apache 2.0',


    packages=find_packages(),
    install_requires=['requests', 'docker-py'],

    scripts=['docker-flow']
)