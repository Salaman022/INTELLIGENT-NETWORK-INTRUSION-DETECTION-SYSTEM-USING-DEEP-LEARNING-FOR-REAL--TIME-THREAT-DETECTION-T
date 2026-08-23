Python 3.13.1 (tags/v3.13.1:0671451, Dec  3 2024, 19:06:28) [MSC v.1942 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license()" for more information.
>>> import json
... import boto3
... dynamodb = boto3.resource('dynamodb')
... table = dynamodb.Table('StudentTable')
... 
... def lambda_handler(event, context):
...     if event['httpMethod'] == 'POST':
...         data = json.loads(event['body'])
...         table.put_item(Item=data)
...         return {
...             'statusCode': 200,
...             'body': json.dumps('Student added')
...         }
... 
...     elif event['httpMethod'] == 'GET':
...         response = table.scan()
...         return {
...             'statusCode': 200,
...             'body': json.dumps(response['Items'])
...         }
