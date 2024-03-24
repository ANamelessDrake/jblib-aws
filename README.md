# jblib-aws

## Author: Justin Bard

This module was written to minimize the need to write the functions I use often.

INSTALL: `python3 -m pip install jblibaws`

---

The source code can be viewed here: [https://github.com/ANamelessDrake/jblib-aws](https://github.com/ANamelessDrake/jblib-aws)

More of my projects can be found here: [http://justbard.com](http://justbard.com)

---

### `talk_with_dynamo`

A class that provides functionality for interacting with AWS DynamoDB tables. It allows you to perform various operations like querying, getting items, updating, inserting, deleting, and scanning the table.

```python
class talk_with_dynamo(table, boto_session, region='us-east-1')

Example:
    table_name = "table-name"
    boto_session = boto3.session.Session()
    dynamo = talk_with_dynamo(table_name, boto_session) # Generate Database Object

    response = dynamo.query(partition_key=None, partition_key_attribute=None, sorting_key=False, 
			sorting_key_attribute=False, index=False, queryOperator=False, 
			betweenValue=False, keyConditionExpression=None, scanIndexForward=True, limit=None):
    print("Response: {}".format(response))

    getResponse = dynamo.getItem(partition_key, partition_key_attribute, sorting_key=False, sorting_key_attribute=False)

    batch_keys = {'tableName': {'Keys': [{'PartitionKey': 'PartitionKeyAttribute', 'SortingKey': 'SortingKey'}]}}
    batchResponse = dynamo.batchGetItem(batch_keys)

    insert_response = dynamo.insert(json_object)
    print("Insert Response: {}".format(insert_response))

    update_response = dynamo.update(partition_key_attribute, sorting_key_attribute, update_key, update_attribute)

    update_response = dynamo.updateV2(partition_key_attribute, update_key, update_attribute, sorting_key_attribute=None)

    delete_response = dynamo.delete(partition_key_attribute, sorting_key_attribute=False, sorting_key=None, partition_key=None)

    scan_results = dynamo.scan(filter_expression=None, expression_attribute_values=None, max_pages=None)

    get_table_description = dynamo.getTableDescription()

    dynamo.clearTable() # Delete all entries in a table -- Use with caution
```

### `extractDynamoDBData`

Extracts and cleans data from a payload retrieved from DynamoDB.

Parameters:

-   payload (dict): The payload containing data retrieved from DynamoDB as a dictionary.
-   record (str): The key to access a specific piece of data within the payload.
-   dataType (str, optional): The type of data to retrieve. Default is "S" (string).

Returns:

-   str or int or False: The extracted and cleaned data based on the specified record and dataType.
-   Returns False if the specified record is not found, or if there is an error during data extraction.

```python
function extractDynamoDBData(payload, record, dataType="S")

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
```

---

### `talk_with_cognito`

A class that provides functionality for interacting with AWS Cognito. It allows you to get a user's email address using their Cognito user ID.

```python
    class talk_with_cognito(boto_client, cognito_user_pool_id)

        Example:

        Functions:
            get_user_email(cognito_user_id)
            - Gets User Email Address

```

### `get_secret`

A function that retrieves a decoded secret from AWS Secrets Manager.

```python
    function get_secret(secret_name, region='us-east-1')

        Example:

        Functions:
            get_secret(secret_name)
            - Returns decoded secret from AWS Secrets Manager

```
