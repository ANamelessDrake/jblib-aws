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
		self.dynamodb_client = self.boto_session.client('dynamodb', region_name=region)
		self.table = self.dynamodb.Table(table)
		self.check_index = check_index
		self.debug = debug

	def query(self, partition_key=None, partition_key_attribute=None, sorting_key=False, 
			sorting_key_attribute=False, index=False, queryOperator=False, 
			betweenValue=False, keyConditionExpression=None, scanIndexForward=True, limit=None):
		"""
		Query a DynamoDB Table with enhanced flexibility via custom KeyConditionExpression.

		:param partition_key: The name of the partition key attribute.
		:param partition_key_attribute: The value of the partition key attribute to query.
		:param sorting_key: (Optional) The name of the sorting key attribute (if using a composite key).
		:param sorting_key_attribute: (Optional) The value of the sorting key attribute to query.
		:param index: (Optional) The name of the Global Secondary Index to use for the query.
		:param queryOperator: (Optional) The query operator to use. Supported values: 'gt', 'gte', 'lt', 'lte', 'between'.
		:param betweenValue: (Optional) A tuple of two values (lowValue, highValue) for the 'between' query operator.
		:param keyConditionExpression: (Optional) A custom KeyConditionExpression for complex query conditions.
		:param scanIndexForward: (Optional) Specifies the order for index traversal: If True (default), the traversal is ascending; if False, the traversal is descending.
		:param limit: (Optional) The maximum number of items to evaluate (not necessarily the number of matching items).
		:return: The response of the query operation.
		"""

		query_params = {
			'KeyConditionExpression': keyConditionExpression or Key(partition_key).eq(partition_key_attribute),
			'ScanIndexForward': scanIndexForward
		}

		if sorting_key and sorting_key_attribute and not keyConditionExpression:
			query_params['KeyConditionExpression'] &= Key(sorting_key).eq(sorting_key_attribute)

		if betweenValue and queryOperator == 'between' and not keyConditionExpression:
			lowValue, highValue = betweenValue
			query_params['KeyConditionExpression'] &= Key(sorting_key).between(lowValue, highValue)

		if index:
			query_params['IndexName'] = index

		if limit:
			query_params['Limit'] = limit

		try:
			response = self.table.query(**query_params)
		except Exception as e:
			print(f"Query failed: {e}")
			response = {}

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

	def updateV2(self, partition_key_attribute, update_key, update_attribute, sorting_key_attribute=None,
				conditionExpression=None, conditionCheck=None, sorting_key=None, max_tries=5,
				additionalUpdateExpressions=None, expressionAttributeValues=None,
				expressionAttributeNames=None, returnValues="UPDATED_NEW",
				partitionKeyName='UniqueID', sortingKeyName='Category'):
		"""
		Enhances the update capability to include dynamic partition and sorting keys.

		:param partition_key_attribute: The value of the partition key for the item to be updated.
		:param update_key: The attribute name that will be updated.
		:param update_attribute: The new value for the update_key.
		:param sorting_key_attribute: The value of the sorting key for the item to be updated, if applicable.
		:param conditionExpression: A condition that must be satisfied for the update to proceed.
		:param conditionCheck: A specific value used in the conditionExpression for comparison.
		:param sorting_key: [Deprecated] Use sorting_key_attribute instead.
		:param max_tries: Number of attempts to make in the face of ProvisionedThroughputExceededException.
		:param additionalUpdateExpressions: Additional expressions for more complex updates.
		:param expressionAttributeValues: A dictionary of attribute values used in the update expression.
		:param expressionAttributeNames: A dictionary of attribute names substitution tokens used in the update expression.
		:param returnValues: Determines what is returned in the response of the update.
		:param partitionKeyName: The name of the partition key (default is 'UniqueID').
		:param sortingKeyName: The name of the sorting key (default is 'Category').
		"""
		key = {partitionKeyName: {'S': partition_key_attribute}}
		if sorting_key_attribute:
			key[sortingKeyName] = {'S': sorting_key_attribute}

		updateExpression = f"SET #k = :a"
		if additionalUpdateExpressions:
			updateExpression += f", {additionalUpdateExpressions}"

		expressionAttributeNames = {"#k": update_key} if not expressionAttributeNames else expressionAttributeNames
		expressionAttributeValues = {':a': {'S': update_attribute}} if not expressionAttributeValues else expressionAttributeValues

		if conditionExpression and conditionCheck and not expressionAttributeValues.get(':condVal'):
			conditionExpression += " AND #k = :condVal"
			expressionAttributeValues[':condVal'] = {'S': conditionCheck}

		for attempt in range(1, max_tries + 1):
			try:
				response = self.table.update_item(
					Key=key,
					UpdateExpression=updateExpression,
					ExpressionAttributeNames=expressionAttributeNames,
					ExpressionAttributeValues=expressionAttributeValues,
					ConditionExpression=conditionExpression if conditionExpression else None,
					ReturnValues=returnValues
				)
				return response
			except Exception as e:
				if attempt < max_tries and "ProvisionedThroughputExceededException" in str(e):
					sleep_time = 2 ** attempt
					time.sleep(sleep_time)
				else:
					raise e

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

	def scan(self, filter_expression=None, expression_attribute_values=None, max_pages=None):
		"""
		Perform a table scan and retrieve items from the DynamoDB Table with an option to limit the number of pages.

		:param filter_expression: (Optional) A string representing the filter expression to apply during the scan.
		:param expression_attribute_values: (Optional) A dictionary representing attribute values used in the filter expression.
		:param max_pages: (Optional) An integer representing the maximum number of pages to retrieve.
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
		pages_processed = 1

		while 'LastEvaluatedKey' in response and (max_pages is None or pages_processed < max_pages):
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
			pages_processed += 1

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

	class TableDescriptionError(Exception):
		"""Custom exception class for table description errors."""
		pass

	def getTableDescription(self):
		"""
		Retrieves the entire description of the DynamoDB Table.

		:return: A dictionary containing the table description.
		:raises: TableDescriptionError if the table description cannot be retrieved.
		"""
		try:
			response = self.dynamodb_client.describe_table(TableName=self.table.name)
			return response
		except Exception as e:
			raise self.TableDescriptionError(f"Failed to get table description: {e}")

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