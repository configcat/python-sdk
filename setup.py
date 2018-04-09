import uuid
from setuptools import setup
from pip.req import parse_requirements

from configcatclient.version import CONFIGCATCLIENT_VERSION

install_reqs = parse_requirements('requirements.txt', session=uuid.uuid1())
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='configcat-client',
    version=CONFIGCATCLIENT_VERSION,
    packages=['configcatclient'],
    url='https://github.com/configcat/python-sdk',
    license='MIT',
    author='ConfigCat',
    author_email='developer@configcat.com',
    description='ConfigCat SDK for Python. https://configcat.com',
    long_description='ConfigCat SDK for Python. https://configcat.com',
    install_requires=reqs,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
    ],
)
