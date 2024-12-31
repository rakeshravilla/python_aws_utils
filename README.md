## Project Structure

```plaintext
/home/rakeshravilla/development/python_aws_utils/
├── README.md
├── src/
│   ├── aws_utils/
│   │   ├── __init__.py
│   │   ├── s3_utils.py
│   │   └── ec2_utils.py
├── tests/
│   ├── test_s3_utils.py
│   └── test_ec2_utils.py
└── .github/
    └── workflows/
        ├── build_and_test.yml
        └── deploy.yml
```

# Python AWS Utils Documentation

## Overview
A collection of Python utilities for working with AWS services, with automated CI/CD through GitHub Actions.

## GitHub Actions Workflows

### Build and Test Workflow
Triggers: 
- Push to main branch
- Pull requests to main branch

Steps:
- Installs Python dependencies
- Runs test suite 
- Performs code quality checks

### Deploy Workflow 
Triggers:
- Push to main branch

Steps:
- Authenticates with AWS
- Deploys application using AWS CLI
