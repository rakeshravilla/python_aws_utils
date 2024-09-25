import json
import boto3
import os
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PipelineManager:
    """Manages the loading and activation of AWS Data Pipelines."""
    
    def __init__(self, config_file):
        self.config_file = config_file
        if not os.path.exists(self.config_file):
            # If config doesn't exist, generate it
            self.pipelines = self.retrieve_pipelines()
            self.write_pipelines_to_file()
        else:
            self.pipelines = self.load_pipeline_config()

    def load_pipeline_config(self):
        """Load pipeline configurations from a JSON file."""
        try:
            with open(self.config_file, 'r') as file:
                config = json.load(file)
                return config.get('pipelines', [])
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON file: {e}")

    def retrieve_pipelines(self):
        """Retrieve pipelines from AWS and store them in the desired format."""
        client = boto3.client('datapipeline')
        pipelines_data = {"pipelines": []}
        
        try:
            response = client.list_pipelines()
            pipelines = response.get('pipelineIdList', [])
            
            for pipeline in pipelines:
                pipeline_id = pipeline['id']
                pipeline_name = pipeline['name']
                parameters = self.get_pipeline_parameters(client, pipeline_id)

                pipeline_info = {
                    "pipeline_id": pipeline_id,
                    "pipeline_name": pipeline_name,
                    "parameterValues": parameters
                }
                pipelines_data["pipelines"].append(pipeline_info)

        except Exception as e:
            logger.error(f"Error retrieving pipelines: {str(e)}")
        
        return pipelines_data["pipelines"]

    def get_pipeline_parameters(self, client, pipeline_id):
        """Retrieve parameter values using get_pipeline_definition for a specific pipeline."""
        parameters = []
        try:
            response = client.get_pipeline_definition(pipelineId=pipeline_id)
            parameter_objects = response.get('parameterObjects', [])
            for param in parameter_objects:
                param_id = param['id']
                param_value = param['attributes'][0].get('stringValue', '')
                parameters.append({
                    'id': param_id,
                    'stringValue': param_value
                })
        except Exception as e:
            logger.error(f"Error retrieving parameters for pipeline {pipeline_id}: {str(e)}")
        return parameters

    def write_pipelines_to_file(self):
        """Write the retrieved pipeline data to a JSON file."""
        try:
            with open(self.config_file, 'w') as json_file:
                json.dump({"pipelines": self.pipelines}, json_file, indent=4)
            logger.info(f"Pipelines data successfully written to {self.config_file}")
        except Exception as e:
            logger.error(f"Error writing to JSON file: {str(e)}")

    def get_pipeline_by(self, key, value):
        """Retrieve a pipeline by a specific key (e.g., 'pipeline_id', 'pipeline_name')."""
        for pipeline in self.pipelines:
            if pipeline[key].lower() == value.lower():
                return pipeline
        return None

    def display_available_pipelines(self):
        """Print available pipelines with their name and ID."""
        print("Available pipelines:")
        for i, pipeline in enumerate(self.pipelines):
            print(f"{i + 1}. {pipeline['pipeline_name']} (ID: {pipeline['pipeline_id']})")

    def select_pipeline_interactively(self):
        """Prompt the user to select a pipeline from the list."""
        self.display_available_pipelines()
        try:
            choice = int(input("Select a pipeline number to activate: ")) - 1
            if 0 <= choice < len(self.pipelines):
                return self.pipelines[choice]
            else:
                print("Invalid selection. Please choose a valid pipeline number.")
                return None
        except ValueError:
            print("Invalid input. Please enter a number.")
            return None


class AWSDataPipelineActivator:
    """Handles AWS Data Pipeline activation using Boto3."""
    
    def __init__(self):
        self.client = boto3.client('datapipeline')

    def activate_pipeline(self, pipeline_id, parameter_values=None, ignore_parameters=False):
        """Activate an AWS Data Pipeline by ID."""
        try:
            if ignore_parameters or not parameter_values:
                response = self.client.activate_pipeline(pipelineId=pipeline_id)
                print(f"Pipeline {pipeline_id} activated without parameters.")
            else:
                response = self.client.activate_pipeline(
                    pipelineId=pipeline_id,
                    parameterValues=parameter_values
                )
                print(f"Pipeline {pipeline_id} activated with parameters.")
            return response
        except Exception as e:
            print(f"Error activating the pipeline: {e}")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Activate AWS Data Pipelines with parameters.")
    parser.add_argument("--pipeline_name", type=str, help="The name of the pipeline to activate.")
    parser.add_argument("--pipeline_id", type=str, help="The ID of the pipeline to activate.")
    parser.add_argument("--config_file", type=str, default="pipeline_config.json", help="Path to the pipeline configuration JSON file.")
    parser.add_argument("--ignore_parameters", action="store_true", help="Ignore parameters when activating the pipeline.")
    return parser.parse_args()


def main():
    """Main function to trigger pipeline activation based on user input or arguments."""
    args = parse_arguments()

    # Initialize the pipeline manager
    manager = PipelineManager(config_file=args.config_file)

    # Select a pipeline based on user input
    selected_pipeline = None
    if args.pipeline_name:
        selected_pipeline = manager.get_pipeline_by('pipeline_name', args.pipeline_name)
    elif args.pipeline_id:
        selected_pipeline = manager.get_pipeline_by('pipeline_id', args.pipeline_id)
    
    # If pipeline is not selected, prompt the user interactively
    if not selected_pipeline:
        selected_pipeline = manager.select_pipeline_interactively()

    # If a pipeline is selected, activate it
    if selected_pipeline:
        activator = AWSDataPipelineActivator()
        pipeline_id = selected_pipeline['pipeline_id']
        parameters = selected_pipeline.get('parameterValues', [])
        activator.activate_pipeline(pipeline_id, parameters, ignore_parameters=args.ignore_parameters)
    else:
        print("No valid pipeline selected.")


if __name__ == "__main__":
    main()
