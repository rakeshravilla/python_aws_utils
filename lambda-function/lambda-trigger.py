import json
import logging
import boto3
import argparse

# Configure logging
logging.basicConfig(filename='lambda_trigger.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

def test_lambda_function(env, payload):
    # Initialize the Lambda client 
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Define the function name dynamically based on the environment
    function_name = f'lambda_test_{env}_run'
    
    logging.info(f"Function name: {function_name}")
    logging.info(f"Test payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Invoke the Lambda function
        response = lambda_client.invoke(
            FunctionName=function_name,  # Dynamic function name
            InvocationType='RequestResponse',   # Synchronous execution
            Payload=json.dumps(payload)
        )
        
        logging.info("Lambda function invoked")
        
        # Read the response
        response_payload = json.loads(response['Payload'].read())
        
        logging.info("Response payload read")
        
        # Check the status code
        status_code = response['StatusCode']
        logging.info(f"Status Code: {status_code}")
        logging.info(f"Response Payload: {json.dumps(response_payload, indent=2)}")
        
        # Check if there was a function error
        if 'FunctionError' in response:
            logging.error(f"Function Error: {response['FunctionError']}")
            
        return response_payload
        
    except Exception as e:
        logging.error(f"Error invoking Lambda function: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Invoke a Lambda function with dynamic parameters.')
    parser.add_argument('--env', required=True, help='The environment name (e.g., dev, prod).')
    parser.add_argument('--pipeline_name', required=True, help='The pipeline name.')
    parser.add_argument('--time_stamp', required=True, help='The timestamp.')

    args = parser.parse_args()

    payload = {
        "pipeline_Name": args.pipeline_name,
        "time_stamp": args.time_stamp,
    }

    test_lambda_function(args.env, payload)
