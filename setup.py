from setuptools import setup


def parse_requirements(filename):
    lines = (line.strip() for line in open(filename))
    return [line for line in lines if line]


configcatclient_version = '9.0.1'

requirements = parse_requirements('requirements.txt')

setup(
    name='configcat-client',
    version=configcatclient_version,
    packages=['configcatclient'],
    url='https://github.com/configcat/python-sdk',
    license='MIT',
    author='ConfigCat',
    author_email='developer@configcat.com',
    description='ConfigCat SDK for Python. https://configcat.com',
    long_description='Feature Flags created by developers for developers with <3. ConfigCat lets you manage '
                     'feature flags across frontend, backend, mobile, and desktop apps without (re)deploying code. '
                     '% rollouts, user targeting, segmentation. Feature toggle SDKs for all main languages. '
                     'Alternative to LaunchDarkly. '
                     'Host yourself, or use the hosted management app at https://configcat.com.',
    install_requires=requirements,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
    ],
)
