import json
import time
import boto3
import datetime
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
		elif isinstance(o, (datetime.date, datetime.datetime)):
			return o.isoformat()
		return super(DecimalEncoder, self).default(o)

class talk_with_dynamo():
	def __init__(self, table, boto_session=None, region='us-east-1', check_index=False, debug=False):
		"""
		Initialize a communication interface with a DynamoDB table using the provided parameters.

		:param table: The name of the DynamoDB table to communicate with.
		:param boto_session: (Optional) The Boto3 session object to use for DynamoDB interactions. If None, a new session will be created.
		:param region: (Optional) The AWS region where the DynamoDB table is located (default is 'us-east-1').
		:param check_index: (Optional) Whether to check the readiness of a global secondary index before querying (default is False).
		:param debug: (Optional) Enable debugging mode to print additional information (default is False).
		"""
		if boto_session is None:
			boto_session = boto3.session.Session()

		self.boto_session = boto_session
		self.dynamodb = self.boto_session.resource('dynamodb', region_name=region)
		self.table = self.dynamodb.Table(table)
		self.check_index = check_index
		self.debug = debug

	def query(self, partition_key, partition_key_attribute, sorting_key=False, sorting_key_attribute=False, index=False, queryOperator=False, betweenValue=False):
		"""
		Query a DynamoDB Table.

		:param partition_key: The name of the partition key attribute.
		:param partition_key_attribute: The value of the partition key attribute to query.
		:param sorting_key: (Optional) The name of the sorting key attribute (if using a composite key).
		:param sorting_key_attribute: (Optional) The value of the sorting key attribute to query.
		:param index: (Optional) The name of the Global Secondary Index to use for the query.
		:param queryOperator: (Optional) The query operator to use. Supported values: 'gt', 'gte', 'lt', 'lte', 'between'.
		:param betweenValue: (Optional) A tuple of two values (lowValue, highValue) for the 'between' query operator.

		:return: The response of the query operation.
		"""

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

		if index and sorting_key and sorting_key_attribute:
			response = self.table.query(
				IndexName=index,
				KeyConditionExpression=Key(partition_key).eq(partition_key_attribute) & Key(sorting_key).eq(sorting_key_attribute),
			)
		elif index:
			response = self.table.query(
				IndexName=index,
				KeyConditionExpression=Key(partition_key).eq(partition_key_attribute),
			)
		elif partition_key and partition_key_attribute and sorting_key and sorting_key_attribute and not queryOperator:
			response = self.table.query(
				KeyConditionExpression=Key(partition_key).eq(partition_key_attribute) & Key(sorting_key).eq(sorting_key_attribute),
			)
		elif partition_key and partition_key_attribute and sorting_key and sorting_key_attribute and queryOperator and not betweenValue:
			if queryOperator == 'gt': 
				response = self.table.query(
					KeyConditionExpression=Key(partition_key).eq(partition_key_attribute) & Key(sorting_key).gt(sorting_key_attribute),
				)
			elif queryOperator == 'gte': 
				response = self.table.query(
					KeyConditionExpression=Key(partition_key).eq(partition_key_attribute) & Key(sorting_key).gte(sorting_key_attribute),
				)
			elif queryOperator == 'lt': 
				response = self.table.query(
					KeyConditionExpression=Key(partition_key).eq(partition_key_attribute) & Key(sorting_key).lt(sorting_key_attribute),
				)
			elif queryOperator == 'lte': 
				response = self.table.query(
					KeyConditionExpression=Key(partition_key).eq(partition_key_attribute) & Key(sorting_key).lte(sorting_key_attribute),
				)
			else:
				response = ""

		elif partition_key and partition_key_attribute and sorting_key and queryOperator and betweenValue:
			if queryOperator == 'between' and betweenValue: 
				lowValue, highValue = betweenValue

				response = self.table.query(
					KeyConditionExpression=Key(partition_key).eq(partition_key_attribute) & Key(sorting_key).between(lowValue, highValue),
				)
			else:
				response = ""
		elif partition_key and partition_key_attribute:
			response = self.table.query(
				KeyConditionExpression=Key(partition_key).eq(partition_key_attribute),
			)
		else:
			response = ""

		return response

	def getItem(self, partition_key, partition_key_attribute, sorting_key=False, sorting_key_attribute=False):
		"""
		Get a single item from the DynamoDB Table.

		:param partition_key: The name of the partition key attribute.
		:param partition_key_attribute: The value of the partition key attribute to retrieve.
		:param sorting_key: (Optional) The name of the sorting key attribute (if using a composite key).
		:param sorting_key_attribute: (Optional) The value of the sorting key attribute to retrieve.

		:return: The response containing the retrieved item or an empty response if the item does not exist.
		"""

		if partition_key and partition_key_attribute and sorting_key and sorting_key_attribute:
			response = self.table.get_item(
				Key={
					partition_key: partition_key_attribute,
					sorting_key: sorting_key_attribute
				}
			)
		elif partition_key and partition_key_attribute:
			response = self.table.get_item(
				Key={
					partition_key: partition_key_attribute
				}
			)
		else:
			response = ""

		return response

	def batchGetItem(self, batch_keys):
		"""
		Get a batch of items from the DynamoDB Table.

		:param batch_keys: The dictionary of batch keys. Each entry in the dictionary should have the table name as the key and a list of key objects as the value.
		:type batch_keys: dict
		:return: The dictionary of retrieved items grouped under their respective table names.
		"""

		tries = 0
		max_tries = 5
		sleepy_time = 1  # Start with 1 second of sleep, then exponentially increase.
		retrieved = {key: [] for key in batch_keys}
		while tries < max_tries:
			response = self.dynamodb.batch_get_item(RequestItems=batch_keys)
			# Collect any retrieved items and retry unprocessed keys.
			for key in response.get('Responses', []):
				retrieved[key] += response['Responses'][key]
			unprocessed = response['UnprocessedKeys']
			if len(unprocessed) > 0:
				batch_keys = unprocessed
				unprocessed_count = sum(
					[len(batch_key['Keys']) for batch_key in batch_keys.values()])
				if self.debug:
					print(f"{unprocessed_count} unprocessed keys returned. Sleep, then retry.")
				tries += 1
				if tries < max_tries:
					if self.debug:
						print(f"Sleeping for {sleepy_time} seconds.")
					time.sleep(sleepy_time)
					sleepy_time = min(sleepy_time * 2, 32)
			else:
				break

		return retrieved

	def update(self, partition_key_attribute, sorting_key_attribute, update_key, update_attribute):
		"""
		[Deprecated] This method is deprecated and should not be used.
		"""
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

	def updateV2(self, partition_key_attribute, update_key, update_attribute, sorting_key_attribute=None, conditionExpression=None, conditionCheck=None, sorting_key=None, max_tries=5):
			"""
			Updates an existing item's attributes or adds a new item to the table if it does not already exist. You can also perform a conditional update on an existing item (insert a new attribute name-value pair if it doesn't exist, or replace an existing name-value pair if it has certain expected attribute values).

			To perform conditional checks against an update call, set `conditionExpression` and `conditionCheck` to the attribute field and attribute value, respectively.
			For example: `conditionExpression='version'` and `conditionCheck=0`

			:param partition_key_attribute: The partition key value of the item to be updated or inserted.
			:param update_key: The name of the attribute to update or add.
			:param update_attribute: The value of the attribute to update or add.
			:param sorting_key_attribute: The optional sorting key value of the item to be updated or inserted.
			:param conditionExpression: (Optional) The name of the attribute to use for conditional update check.
			:param conditionCheck: (Optional) The expected value of the attribute for the conditional update.
			:param sorting_key: (Optional) The name of the sorting key attribute, if different from the default 'Category'.
			:param max_tries: (Optional) The maximum number of retries in case of throttling or other transient errors (default is 5).
			:return: The response of the update operation. If the update is conditional and fails, it will return {'error': 'ConditionalCheckFailedException'}.

			Example usage:
			```
			# Update an existing item's attribute 'version' with the new value '2'
			response = updateV2(partition_key_attribute='item_id', update_key='version', update_attribute=2)

			# Add a new item with partition key 'item_id' and sorting key 'category' with the attribute 'price' set to 10
			response = updateV2(partition_key_attribute='item_id', update_key='price', update_attribute=10, sorting_key_attribute='category')
			```
			"""
			key = {}
			key['UniqueID'] = partition_key_attribute

			if sorting_key_attribute is not None:
				if sorting_key:
					key[sorting_key] = sorting_key_attribute
				else:
					key['Category'] = sorting_key_attribute

			for attempt in range(1, max_tries + 1):
				try:
					if conditionExpression and conditionCheck:
						response = self.table.update_item(
							Key=key,
							UpdateExpression="set #k = :a",
							ExpressionAttributeNames={
								"#k": update_key
							},
							ExpressionAttributeValues={
								':a': update_attribute
							},
							ConditionExpression=Attr(conditionExpression).eq(conditionCheck),
							ReturnValues="UPDATED_NEW"
						)
					else:
						response = self.table.update_item(
							Key=key,
							UpdateExpression="set #k = :a",
							ExpressionAttributeNames={
								"#k": update_key
							},
							ExpressionAttributeValues={
								':a': update_attribute
							},
							ReturnValues="UPDATED_NEW"
						)
					return response
				except Exception as e:
					if attempt < max_tries and "ProvisionedThroughputExceededException" in str(e):
						# Exponential backoff for throttling errors
						sleep_time = 2 ** attempt
						time.sleep(sleep_time)
					else:
						# If it's not a throttling error or max retries are reached, raise the exception or return an error response.
						if "ConditionalCheckFailedException" in str(e):
							return {'error': 'ConditionalCheckFailedException'}
						else:
							return {'error': str(e)}

	def insert(self, payload):
		"""
		Insert an item into the DynamoDB Table.

		:param payload: The dictionary representing the item to be inserted.
		:type payload: dict
		:return: The response of the insert operation.
		"""

		response = self.table.put_item(Item=payload)

		return response

	def delete(self, partition_key_attribute, sorting_key_attribute=False, sorting_key=None, partition_key=None):
		"""
		Delete an item from the DynamoDB Table.

		:param partition_key_attribute: The value of the partition key attribute for the item to delete.
		:param sorting_key_attribute: (Optional) The value of the sorting key attribute for the item to delete.
		:param sorting_key: (Optional) The name of the sorting key attribute, if different from the default 'Category'.
		:param partition_key: (Optional) The name of the partition key attribute, if different from the default 'UniqueID'.
		:return: The response of the delete operation.
		"""

		key = {}

		if partition_key:
			key[partition_key] = partition_key_attribute
		else:
			key['UniqueID'] = partition_key_attribute

		if sorting_key_attribute or sorting_key_attribute == 0:
			if sorting_key:
				key[sorting_key] = sorting_key_attribute
			else:
				key['Category'] = sorting_key_attribute
		
		response = self.table.delete_item(
			Key=key
		)
		return response

	def scan(self, filter_expression=None, expression_attribute_values=None):
		"""
		Perform a table scan and retrieve items from the DynamoDB Table.

		:param filter_expression: (Optional) A string representing the filter expression to apply during the scan.
		:param expression_attribute_values: (Optional) A dictionary representing attribute values used in the filter expression.
		:return: A list containing items that match the scan criteria.
		"""
		if filter_expression and expression_attribute_values:
			response = self.table.scan(
				FilterExpression=filter_expression,
				ExpressionAttributeValues=expression_attribute_values
			)
		elif filter_expression:
			response = self.table.scan(FilterExpression=filter_expression)
		else:
			response = self.table.scan()

		data = response['Items']

		while 'LastEvaluatedKey' in response:
			if filter_expression and expression_attribute_values:
				response = self.table.scan(
					FilterExpression=filter_expression,
					ExpressionAttributeValues=expression_attribute_values,
					ExclusiveStartKey=response['LastEvaluatedKey']
				)
			elif filter_expression:
				response = self.table.scan(
					FilterExpression=filter_expression,
					ExclusiveStartKey=response['LastEvaluatedKey']
				)
			else:
				response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])

			data.extend(response['Items'])

		return data

	def clearTable(self):
		"""
		[Warning] This will clear all entries from the table. Use with caution!!!

		:return: None
		"""

		tableKeyNames = [key.get("AttributeName") for key in self.table.key_schema]

		#Only retrieve the keys for each item in the table (minimize data transfer)
		projectionExpression = ", ".join('#' + key for key in tableKeyNames)
		expressionAttrNames = {'#'+key: key for key in tableKeyNames}
		
		counter = 0
		page = self.table.scan(ProjectionExpression=projectionExpression, ExpressionAttributeNames=expressionAttrNames)
		with self.table.batch_writer() as batch:
			while page["Count"] > 0:
				counter += page["Count"]
				# Delete items in batches
				for itemKeys in page["Items"]:
					batch.delete_item(Key=itemKeys)
				# Fetch the next page
				if 'LastEvaluatedKey' in page:
					page = self.table.scan(
						ProjectionExpression=projectionExpression, ExpressionAttributeNames=expressionAttrNames,
						ExclusiveStartKey=page['LastEvaluatedKey'])
				else:
					break
		print(f"Deleted {counter} rows...")

def extractDynamoDBData(payload, record, dataType="S"):
	"""
	Extracts and cleans data from a payload retrieved from DynamoDB.

	Parameters:
		payload (dict): The payload containing data retrieved from DynamoDB as a dictionary.
		record (str): The key to access a specific piece of data within the payload.
		dataType (str, optional): The type of data to retrieve. Default is "S" (string).

	Returns:
		str or int or False: The extracted and cleaned data based on the specified record and dataType.
		Returns False if the specified record is not found, or if there is an error during data extraction.

	Raises:
		None: The function handles exceptions internally and returns False if any error occurs.

	Example:
		payload = {
			"name": "John Doe",
			"age": {
				"N": "30"
			},
			"address": "123 Main Street"
		}
		data = returnData(payload, "name")
		print(data)  # Output: "John Doe"

		data = returnData(payload, "age", dataType="N")
		print(data)  # Output: 30

		data = returnData(payload, "email")
		print(data)  # Output: False (record not found in payload)
	"""
	try:
		data = payload.get(record, False)
		if data:
			data = data.get(dataType, False)

			if dataType == "N":
				if not data:
					data = 0
				else:
					data = int(data)

		return data
	except Exception as e:
		print(f'Failed while attempting to clean DynamoDB data: {e}\nPayload: {payload} -- Record: {record} -- Data Type: {dataType}')
		return False