# Contributing to the ConfigCat SDK for Python

ConfigCat SDK is an open source project. Feedback and contribution are welcome. Contributions are made to this repo via Issues and Pull Requests.

## Submitting bug reports and feature requests

The ConfigCat SDK team monitors the [issue tracker](https://github.com/configcat/python-sdk/issues) in the SDK repository. Bug reports and feature requests specific to this SDK should be filed in this issue tracker. The team will respond to all newly filed issues.

## Submitting pull requests

We encourage pull requests and other contributions from the community. 
- Before submitting pull requests, ensure that all temporary or unintended code is removed.
- Be accompanied by a complete Pull Request template (loaded automatically when a PR is created).
- Add unit or integration tests for fixed or changed functionality.

When you submit a pull request or otherwise seek to include your change in the repository, you waive all your intellectual property rights, including your copyright and patent claims for the submission. For more details please read the [contribution agreement](https://github.com/configcat/legal/blob/main/contribution-agreement.md).

In general, we follow the ["fork-and-pull" Git workflow](https://github.com/susam/gitpr)

1. Fork the repository to your own Github account
2. Clone the project to your machine
3. Create a branch locally with a succinct but descriptive name
4. Commit changes to the branch
5. Following any formatting and testing guidelines specific to this repo
6. Push changes to your fork
7. Open a PR in our repository and follow the PR template so that we can efficiently review the changes.

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

## Running tests against all supported Python versions and linters

There is a [tox](https://tox.wiki/) configuration file allowing to test against all supported Python versions
as well as linting all files in isolated environments.

Just run:

```bash
# Test against all supported Python versions and lint
tox 
# Test against a given Python version
tox -e py310
# Lint
tox -e lint 
```
