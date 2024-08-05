import json

class talk_with_cognito():
    def __init__(self, boto_client, cognito_user_pool_id, debug=False):
        """
        Initializes a new instance of the talk_with_cognito class.

        Parameters:
            boto_client (boto3.client): The Boto3 client object used to interact with Cognito.
            cognito_user_pool_id (str): The ID of the Cognito user pool.
            debug (bool, optional): Whether to enable debug mode. Defaults to False.
        """
        # Initialize the Boto3 client object for Cognito
        self.boto_client = boto_client

        # Set the ID of the Cognito user pool
        self.cognito_user_pool_id = cognito_user_pool_id

        # Set the debug mode flag
        self.debug = debug
    def get_user_email(self, cognito_user_id):
        """
        Retrieves the user email and email verification status from Cognito user attributes.

        Parameters:
            cognito_user_id (str): The Cognito user ID to retrieve information for.

        Returns:
            tuple: A tuple containing the user email (str) and the email verification status (bool).
        """
        # Send a request to Cognito to retrieve user attributes
        cognito_response = self.boto_client.admin_get_user(
            UserPoolId=self.cognito_user_pool_id,
            Username=cognito_user_id
        )

        # If debug mode is enabled, print the response from Cognito
        if self.debug:
            print("Cognito Response: {}".format(json.dumps(cognito_response,  default=str)))

        # Convert the response from JSON to a Python dictionary
        cognito_response = json.loads(json.dumps(cognito_response,  default=str))

        # Initialize variables to store user email and email verification status
        cognito_email_verified = None
        cognito_user_email = None

        # Iterate through the user attributes and extract the email and email verification status
        for data in cognito_response['UserAttributes']:
            if data['Name'] == 'email':
                cognito_user_email = data['Value']
            elif data['Name'] == 'email_verified':
                cognito_email_verified = data['Value']
                if cognito_email_verified == 'true':
                    cognito_email_verified = True
                else:
                    cognito_email_verified = False

        # Return the user email and email verification status
        return cognito_user_email, cognito_email_verified
