# Travel Planner
================

## Authors:
- [Armando Diaz](https://www.linkedin.com/in/armando-diaz-47a498113/) @armdiazg 
- [Marco Punio](https://www.linkedin.com/in/marcpunio/) @puniomp
- [Jorge Rojas](https://www.linkedin.com/in/jorgealerojas/) @jorgealerojas

This guide details how to install, configure, and use the agent CDK deployment. The instructions assume that the deployment will be deployed from a terminal running from Linux or MacOS.

Resources provisioned by deployment:

* S3 bucket
* Bedrock Agent
* Bedrock Agent IAM role
* Two Bedrock Agent Action Groups (Travel and Portfolio)
* Two Lambda functions (Travel and Portfolio)
* Lambda service-policy permissions
* Lambda IAM roles

The tutorial deploys Bedrock agent backed by Anthropic Claude V2 model and creates two Action Groups within this agent:
1. Travel API: For searching flights and hotels using schemas in `lib/assets/api-schema/travel_schema.json`
2. Portfolio API: For checking stock portfolio value using schemas in `lib/assets/api-schema/portfolio_schema.json`

The Python functions for these APIs are located in `lib/assets/lambda`. To deploy, the demo creates an S3 bucket and uploads schemas to it. IAM roles are provisioned by CDK. Make sure to modify the policies appropriate for your needs.

# Prerequisites
===============

* [SerpApi API Key](https://serpapi.com/)
   1) Go to https://serpapi.com/dashboard
   2) Sign in to your Serp API account or create one if you don't have it.
   3) In your dashboard, generate an API key. This key will be essential for accessing the Serp API services and stack deployment.
* [node](https://nodejs.org/en) >= 16.0.0
* [npm](https://www.npmjs.com/) >= 8.0.0
* [AWS CLI](https://aws.amazon.com/cli/) >= 2.0.0
* [AWS CDK](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-construct-library.html) >= 2.130.0
* [Docker](https://www.docker.com/):
   - Install [Docker](https://docs.docker.com/desktop/) or
   - Create an [AWS Cloud9](https://docs.aws.amazon.com/cloud9/latest/user-guide/create-environment-main.html) environment

*Note: In some cases, you might need to authenticate Docker to Amazon ECR registry with get-login-password. Run the aws ecr [get-login-password](https://docs.aws.amazon.com/AmazonECR/latest/userguide/getting-started-cli.html) command. `aws ecr get-login-password --region region | docker login --username AWS --password-stdin aws_account_id.dkr.ecr.region.amazonaws.com`*

# How to run

From within the root project folder (``travel-planner``), run the following commands:

```sh
npm install
```
Note - if you have `npm ERR!` errors related to overlapping dependencies, run `npm install --force`.
```sh
cdk bootstrap
```

Substitute "my-api-key" with your SerpApi Api Key and configure your stock portfolio:
```sh
export STOCK_PORTFOLIO='{"AAPL": 10, "GOOGL": 5, "MSFT": 8}'  # Example portfolio configuration
cdk deploy -c apiKey="my-api-key"
```

Optional - if you want to change the [default settings](lib/constants.ts) you can deploy the stack like this (substituting values as needed):

```sh
cdk deploy -c agentName="my-agent-name" -c apiKey="my-api-key" -c agentInstruction="my-agent-instruction" -c agentModel="my-agent-model" -c agentDescription="my-agent-description"
```

# Sample prompts:

## Travel Planning
+ *What is the cheapest flight from Atlanta to Miami in October, 2024?*
+ *Can you find me a hotel under $150/night in San Francisco from December 4th to December 15th, 2024?*

## Portfolio Checking
+ *What's the current value of my stock portfolio?*
+ *Can I afford a $5000 trip to Europe based on my current portfolio value?*
+ *How much would I have left in my portfolio after spending $3000 on travel?*

# Features

## Travel Planning
- Search for flights using Google Flights API
- Find hotels and accommodations using Google Hotels API
- Get detailed pricing and availability information

## Portfolio Management
- Real-time stock price checking using Google Finance
- Portfolio value calculation
- Travel budget feasibility analysis
- Remaining portfolio value estimation after travel expenses

# Automatic OpenAPI generator with Powertools for AWS Lambda (Python):

The [OpenAPI schema](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-api-schema.html) defines the APIs that the agent can invoke. You can create your own OpenAPI schema following our examples in:
- Travel API: [lib/assets/api-schema/create_openapi_schema.py](lib/assets/api-schema/create_openapi_schema.py)
- Portfolio API: [lib/assets/lambda/portfolio_agent.py](lib/assets/lambda/portfolio_agent.py)

Both use [Powertools for AWS Lambda](https://github.com/aws-powertools/powertools-lambda-python) to autogenerate OpenAPI schemas.

# Environment Variables

## Required
- `API_KEY`: Your SerpApi API key

## Optional
- `STOCK_PORTFOLIO`: JSON string containing your stock portfolio configuration
  ```json
  {
    "AAPL": 10,    // 10 shares of Apple
    "GOOGL": 5,    // 5 shares of Google
    "MSFT": 8      // 8 shares of Microsoft
  }
  ```

# How to delete

From within the root project folder (``travel-planner``), run the following command:

```sh
cdk destroy --force
```

**Note - if you created any aliases/versions within your agent you would have to manually delete it in the console.**
