# Exporting to AWS Lambda

This folder contains all necessary files to export to AWS Lambda.

## Pre-requisites

* docker CLI
* aws CLI
* [sam CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)

## Layout

* `app.py` - Lambda's code
* `Dockerfile` - Used to build the docker image to deploy
* `template.yaml` - Lambda configuration

## Building image

To build an image:

```sh
invoke aws-lambda-build
```

Note that the previous command runs `test_aws_lambda.py` before building,
generates a `.whl` file from your project and then calls `sam build`. For
details, see the implementation in the `tasks.py` file in your project's root
directory.

If the building process finishes correctly, you'll see the image listed here:

```sh
docker images
```

## Testing locally

```sh
cd aws-lambda
sam local start-api
```

Once initialized, you can use `curl` or similar to test your endpoint:

```sh
# by default, the endpoint is exposed in /predict and configured as POST
curl http://127.0.0.1:3000/predict -X POST -d '{"some": "data"}'
```

## Deployment

```sh
sam build
```
