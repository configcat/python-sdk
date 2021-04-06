# Contributing to the ConfigCat SDK for Python

ConfigCat SDK is an open source project. Feedback and contribution are welcome. The information below describes how to build the project with your changes, run the tests, and send the Pull Request.

## Submitting bug reports and feature requests

The ConfigCat SDK team monitors the [issue tracker](https://github.com/configcat/python-sdk/issues) in the SDK repository. Bug reports and feature requests specific to this SDK should be filed in this issue tracker. The team will respond to all newly filed issues.

## Submitting pull requests

We encourage pull requests and other contributions from the community. Before submitting pull requests, ensure that all temporary or unintended code is removed.

## Build instructions

It's advisable to create a virtual development environment within the project directory:

```bash
python -m venv venv
source venv/bin/activate
```

To install requirements:

```bash
pip install -r requirements.txt
pip install pytest mock
```

## Running tests

```bash
pytest configcatclienttests
```
