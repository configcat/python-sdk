from setuptools import setup

def parse_requirements(filename):
    lines = (line.strip() for line in open(filename))
    return [line for line in lines if line]

configcatclient_version="2.1.1"

reqs = parse_requirements('requirements.txt')

setup(
    name='configcat-client',
    version=configcatclient_version,
    packages=['configcatclient'],
    url='https://github.com/configcat/python-sdk',
    license='MIT',
    author='ConfigCat',
    author_email='developer@configcat.com',
    description='ConfigCat SDK for Python. https://configcat.com',
    long_description='ConfigCat is a configuration as a service that lets you manage your features and configurations without actually deploying new code.',
    install_requires=reqs,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
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
