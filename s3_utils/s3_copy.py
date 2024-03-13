import csv
import boto3
import logging

# Configure logging
logging.basicConfig(filename='s3_copy.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def copy_s3_objects(source_bucket, source_key, destination_bucket, destination_key):
    s3 = boto3.client('s3')
    copy_source = {'Bucket': source_bucket, 'Key': source_key}
    try:
        s3.copy(copy_source, destination_bucket, destination_key)
        logging.info(f"Copied '{source_key}' from '{source_bucket}' to '{destination_key}' in '{destination_bucket}'.")
        return True
    except Exception as e:
        logging.error(f"Error copying '{source_key}' from '{source_bucket}' to '{destination_key}' in '{destination_bucket}': {e}")
        return False

def move_s3_objects(source_bucket, source_key, destination_bucket, destination_key):
    if copy_s3_objects(source_bucket, source_key, destination_bucket, destination_key):
        s3 = boto3.client('s3')
        try:
            s3.delete_object(Bucket=source_bucket, Key=source_key)
            logging.info(f"Moved '{source_key}' from '{source_bucket}' to '{destination_key}' in '{destination_bucket}'. Original object deleted.")
        except Exception as e:
            logging.error(f"Error deleting original object '{source_key}' from '{source_bucket}': {e}")
    else:
        logging.error(f"Move operation failed for '{source_key}' from '{source_bucket}' to '{destination_key}' in '{destination_bucket}'. Original object not deleted.")

def main():
    # Path to your CSV file containing source and destination paths
    csv_file = 's3_paths.csv'

    # Accessing AWS credentials
    aws_access_key_id = 'your_access_key_id'
    aws_secret_access_key = 'your_secret_access_key'

    # Reading CSV file
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            source_bucket, source_key, destination_bucket, destination_key = row
            move_s3_objects(source_bucket, source_key, destination_bucket, destination_key)

if __name__ == "__main__":
    main()
