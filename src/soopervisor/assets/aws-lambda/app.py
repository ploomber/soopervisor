import json

import pandas as pd
from ploomber import OnlineModel

import {{package_name}}

model = OnlineModel({{package_name}})


def handler(event, context):
    body = json.loads(event['body'])

    raise NotImplementedError('Missing implementation '
                              'in {{package_name}}/app.py. '
                              'Add input parsing logic.')

    # NOTE: example implementation for a pipeline that expects a data frame
    # in a "get" task input
    df = pd.DataFrame(body, index=[0])
    prediction = int(model.predict(get=df)[0])

    return {
        "statusCode": 200,
        "body": json.dumps({
            "prediction": prediction
        }),
    }
