# Protoype - Github actions

Developing the actual CI service with Jenkins X is going to take a while. But we can protoype the workflow to get quick feedback using Github Actions.

For lack of a better name, I'm calling this tool "soopervisor" temporarily.

## Objective

`git push` triggers a github actions that:

1. Looks for an `environment.yml`, install dependencies
2. Activate environment
3. Look for a `setup.py`, if found call `pip install .`
4. If ploomber not installed, do `pip install ploomber`
5. Execute pipeline `ploomber entry pipeline.yaml` (sample=True)
6. Copy contents of `/output` to `/path/to/storage/{commit-hash}`
7. A comment in the PR triggers a run with (sample=False)
8. Uploads artifacts to a folder in cloud storage `project/{commit-hash}`
9. We can download artifacts using a CLI

Limitations: Github actions run in a VM with 14GB of disk, 2 CPUs and 7 GB of RAM ([Source](https://help.github.com/en/actions/reference/virtual-environments-for-github-hosted-runners)).

About storage: since we hope this to be used mostly by individual users (and not companies), we have to provide options for services that have a free tier: google drive and dropbox.

Before doing any processing, the tool should verify that all required files exist to save time: `environment.yml`, `pipeline.yaml`


## First phase local development

To facilitate development, we'll first develop a local tool that will perform the same workflow but inside a local docker container.

### API

```
soopervisor /path/to/repo/ --dropbox/--gdrive/{/local/path}
```

### Architecture ideas

My original idea was to keep the container open and just send commands, one at a time, but that might not be the best idea.

I think what Travis CI does is a clean option, they generate a bash file based on a `.travis.yml` (https://github.com/travis-ci/travis-build). Our tool does not require a user config file but we can still follow that approach.

Make a Python script generate a bash script. Then send the script to the Docker container for execution and stream output.

Important: credentials should not be visible from the logs.

### Tools

* pytest for testing
* docker-py https://github.com/docker/docker-py


**Best options: onedrive and box**

We need a service with a free tier that doesn't require users to do anything else beyond creating the account to be able to upload things using Python.

One Drive looks good, sdk: https://github.com/OneDrive/onedrive-sdk-python I don't see anything about file size limit

Box SDK also looks good: https://github.com/box/box-python-sdk free accounts gives you 10GB, with a 250MB limit per file


**Google Drive**

https://developers.google.com/drive/api/v3/quickstart/python
This library is supposed to make things easier: https://pythonhosted.org/PyDrive/quickstart.html

Why does the documentation say "Click this button to create a new Cloud Platform project and automatically enable the Drive API", does this mean individual accounts cannot use this?

**Dropbox client**

https://www.dropbox.com/developers/documentation/python 

dropbox offers only 2gb in the free plan, might not be a great option)

## Second phase: Github action

Use the tool from the previous phase and implement it as a Github action.

Also add the option of triggering a run with (sample=False) by adding a comment in a PR. See this: https://fastpages.fast.ai/actions/markdown/2020/03/06/fastpages-actions.html

## Third phase: remote deployment

Develop this as a server app that polls a list of repositories. The idea is to have something as simple as possible that can reflect the previous phase without having to depend on github actions computational limitations. This should be an easy to deploy app for companies that don't want their code to leave their network, but we could possibly offer this as as a cloud service.


## Timeline

This is tentative and subject to change, our top priority is a well-documented tool with great user experience, not meeting deadlines.





