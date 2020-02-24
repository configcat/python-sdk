# Steps to deploy
## Preparation
1. Run tests
   ```bash
   py.test configcatclienttests
   ```
2. Increase the version of the library with the `version_update.sh` script.
   ```bash
   ./version_update.sh x.x.x
   ```
## Publish
Use the **same version** for the git tag as in the `configcatclient/version.py`.
- Via git tag
    1. Create a new version tag.
       ```bash
       git tag v[MAJOR].[MINOR].[PATCH]
       ```
       > Example: `git tag v2.5.5`
    2. Push the tag.
       ```bash
       git push origin --tags
       ```
- Via Github release 

  Create a new [Github release](https://github.com/configcat/python-sdk/releases) with a new version tag and release notes.

## Python Package
Make sure the new version is available on [PyPI](https://pypi.org/project/configcat-client/).
