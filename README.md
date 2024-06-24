# Introduction 
This is for integrating Maltego with a MISP Instance.

## Getting Started
1. There are two possible ways to deploy:
   - Local Deployment
   - iTDS Deployment
2. Software dependencies:
   - Python v3.12
   - Maltego-trx
   - PyMISP
   - python-dotenv
   - Docker

3. API references:
   - [MISP OpenAPI](https://www.misp-project.org/openapi/)
   - [MISP Data Models](https://www.misp-project.org/datamodels/)


## Running The Transform Server

### Development Deployment:

Edit the extensions.py to point it to the correct transform host server
You can start the development server by running the following command:

      python project.py runserver

This will start up a development server that automatically reloads every time the code is changed.

### Production Deployment:

You can run a gunicorn transform server after installing gunicorn on the host machine and then running the command:

      gunicorn --bind=0.0.0.0:8080 --threads=25 --workers=2 project:application

For publicly accessible servers, it is recommended to run your Gunicorn server behind proxy servers such as Nginx.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Local Deployment: [Local Transform](https://docs.maltego.com/support/solutions/articles/15000010781-local-transforms)

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;iTDS Deployment: [iTDS Transform](https://docs.maltego.com/support/solutions/articles/15000034027-development-transform-server)

### Configuration

Create a file named .env in the same directory as your Python script (project.py). This file will store sensitive information like API keys.
Alternatively, you can also use transform settings to set the URL and API key.

Follow the instructions here to add seeds, config.mtz files, and transforms.
[iTDS Transform Setup](https://docs.maltego.com/support/solutions/articles/15000034133-seeds)

Start the development server (for testing):

      python project.py runserver

This will start a server on http://localhost:8080 by default. 

For production deployment, consult the Gunicorn documentation for recommended practices

### Troubleshooting

Common errors might include:

    Connection errors: Verify your MISP URL and ensure the server is reachable.
    Authentication errors: Double-check your API key in the .env file.
    For detailed error messages, consult the Maltego transform logs and MISP API documentation.
