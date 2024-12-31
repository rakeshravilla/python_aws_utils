import os
import yaml
import boto3
import base64
import logging
from datetime import datetime

# Configure logging
LOG_FILE = "pipeline_execution.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def load_yaml(file_path):
    """Load the YAML file."""
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def get_pipelines_for_phase(data, client_name, phase):
    """Retrieve pipelines for a given client and phase."""
    client_data = data['clients'].get(client_name, [])
    pipelines = next((p['pipelines'] for p in client_data if p['phase'] == phase), [])
    return pipelines

def invoke_lambda(lambda_client, function_name, payload):
    """Invoke an AWS Lambda function and return the decoded logs."""
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        LogType='Tail',
        Payload=bytes(str(payload), encoding='utf-8')
    )
    log_result = base64.b64decode(response['LogResult']).decode('utf-8')
    return log_result

def main():
    # Load the YAML file
    yaml_file = "pipelines.yaml"
    if not os.path.isfile(yaml_file):
        logging.error(f"YAML file '{yaml_file}' not found!")
        exit(1)

    data = load_yaml(yaml_file)
    logging.info("YAML file loaded successfully.")

    # User input
    client_name = input("Enter your client name: ").strip()
    if client_name not in data['clients']:
        logging.error(f"No data found for client '{client_name}'!")
        exit(1)

    try:
        phase = int(input("Enter the phase number (1-9): ").strip())
    except ValueError:
        logging.error("Invalid phase number. Please enter a number between 1 and 9.")
        exit(1)

    pipelines = get_pipelines_for_phase(data, client_name, phase)
    if not pipelines:
        logging.error(f"No pipelines found for client '{client_name}' and phase {phase}!")
        exit(1)

    env = input("Which environment are you running? (uat, sit, ppr): ").strip().upper()
    date_input = input("Enter the date (yyyyMMdd): ").strip()
    time_input = input("Enter the time (HH:MM, default 18:00): ").strip() or "18:00"

    # Format date and time
    date_formatted = f"{date_input[:4]}-{date_input[4:6]}-{date_input[6:8]}"
    datetime_str = f"{date_formatted}T{time_input}:00Z"
    logging.info(f"Date and time set to {datetime_str}.")

    # Initialize boto3 Lambda client
    lambda_client = boto3.client('lambda')
    logging.info("AWS Lambda client initialized.")

    # Process pipelines
    for pipeline in pipelines:
        pipeline_name = f"{env}_{pipeline}"
        logging.info(f"Processing pipeline: {pipeline_name}")

        payload = {
            "time": datetime_str,
            "detail": {
                "pipelinesToRunByName": pipeline_name
            }
        }

        try:
            # Invoke Lambda function
            function_name = f"InboundFileHandler_{env}_dataPipelineTriggerHandler"
            log_result = invoke_lambda(lambda_client, function_name, payload)

            # Log the Lambda output
            logging.info(f"Lambda output for pipeline '{pipeline_name}':\n{log_result}")

            if "ActivationSuccess" in log_result:
                logging.info(f"Pipeline '{pipeline_name}' triggered successfully.")
            elif "ActivationNone" in log_result:
                logging.warning(f"Pipeline '{pipeline_name}' not triggered.")
            else:
                logging.error(f"Trigger failed for pipeline '{pipeline_name}'.")

        except Exception as e:
            logging.error(f"Error processing pipeline '{pipeline_name}': {e}")

if __name__ == "__main__":
    main()
