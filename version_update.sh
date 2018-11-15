#!/usr/bin/env bash
# The deploy scripts takes one argument: the version for the client lib.
# It should be run from the root of the repo:
# bash .\version_update.sh x.x.x

set -uxe

#Update version in configcatclient/version.py
echo "CONFIGCATCLIENT_VERSION = \"$1\"" > configcatclient/version.py

#Update version in configcatclient/setup.py
sed "s/configcatclient_version=.*/configcatclient_version=\"$1\"/g" setup.py > setup.py.tmp
mv setup.py.tmp setup.py

echo "Commit and push changes"
