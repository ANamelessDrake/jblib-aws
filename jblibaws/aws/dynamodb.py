import json
import boto3
from datetime import datetime
from decimal import Decimal
from time import sleep
from boto3.dynamodb.conditions import Key, Attr

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if abs(o) % 1 > 0:
                return float(o)
            else:
                return int(o)
        elif isinstance(o, list):
            for i in xrange(len(o)):
                o[i] = self.default(o[i])
            return o
        elif isinstance(o, set):
            new_list = []
            for index, data in enumerate(o):
                new_list.append(self.default(data))
                
            return new_list
        elif isinstance(o, dict):
            for k in o.iterkeys():
                o[k] = self.default(o[k])
            return o
        elif isinstance(o, (datetime.date, datetime)):
            return o.isoformat()
        return super(DecimalEncoder, self).default(o)

class talk_with_dynamo():
    def __init__(self, table, boto_session, region='us-east-1', check_index=False):
        self.boto_session = boto_session
        self.dynamodb = self.boto_session.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table)
        self.check_index = check_index

        self.boto_client = boto3.client('dynamodb') # Legacy - Used for legacy insert functionality - Remove once session can be used
                # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html

    def query(self, partition_key, partition_key_attribute, sorting_key=False, sorting_key_attribute=False, index=False):
        if self.check_index:
            # When adding a global secondary index to an existing table, you cannot query the index until it has been backfilled.
            # This portion of the script waits until the index is in the “ACTIVE” status, indicating it is ready to be queried.
            while True:
                if not self.table.global_secondary_indexes or self.table.global_secondary_indexes[0]['IndexStatus'] != 'ACTIVE':
                    print('[{}]  Waiting for index to backfill...'.format('INFO'))
                    sleep(5)
                    self.table.reload()
                else:
                    break

        if index:
            response = self.table.query(
                IndexName=index,
                KeyConditionExpression=Key(partition_key).eq(partition_key_attribute),
            )
        elif index and sorting_key and sorting_key_attribute:
            response = self.table.query(
                IndexName=index,
                KeyConditionExpression=Key(partition_key).eq(partition_key_attribute) & Key(sorting_key).eq(sorting_key_attribute),
            )
        elif partition_key and partition_key_attribute and sorting_key and sorting_key_attribute:
            response = self.table.query(
                KeyConditionExpression=Key(partition_key).eq(partition_key_attribute) & Key(sorting_key).eq(sorting_key_attribute),
            )
        elif partition_key and partition_key_attribute:
            response = self.table.query(
                KeyConditionExpression=Key(partition_key).eq(partition_key_attribute),
            )
        else:
            response = ""

        return response

    def update(self, partition_key_attribute, sorting_key_attribute, update_key, update_attribute):
        response = self.table.update_item(
            Key={
               'UniqueID': partition_key_attribute,
               'Category': sorting_key_attribute
            },
            UpdateExpression="set #k = :a",
            ExpressionAttributeNames = {
                "#k" : update_key
            },
            ExpressionAttributeValues={
                ':a': update_attribute
            },
            ReturnValues="UPDATED_NEW"
        )
        return response

    def insert(self, payload):
        response = self.table.put_item(Item=payload)
        return response
