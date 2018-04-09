#!/usr/bin/env bash
# The deploy scripts takes one argument: the version for the client lib.
# It should be run from the root of the repo:
# bash .\scripts\dist.sh 1.0.0
# You should set up your .pypirc before executing this script

set -uxe

echo "Starting ConfigCat-Client "$1" distribution"

#Update version in configcatclient/version.py
echo "CONFIGCATCLIENT_VERSION = \"$1\"" > configcatclient/version.py

python setup.py sdist upload

echo "Done with ConfigCat-Client distribution"
echo "Commit and push changes"
