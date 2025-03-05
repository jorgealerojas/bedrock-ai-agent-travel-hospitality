import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { S3Construct } from './constructs/s3-bucket-construct';
import { BedrockIamConstruct } from './constructs/bedrock-agent-iam-construct';
import { LambdaIamConstruct } from './constructs/lambda-iam-construct';
import { LambdaConstruct } from './constructs/lambda-construct';
import { BedrockAgentConstruct } from './constructs/bedrock-agent-construct';

import { AGENT_NAME, API_KEY, AGENT_INSTRUCTION, AGENT_MODEL, AGENT_DESCRIPTION } from './constants';

export interface BedrockAgentCdkProps extends cdk.StackProps {
  readonly travelSpecFile: string;
  readonly portfolioSpecFile: string;
  readonly travelLambdaFile: string;
  readonly portfolioLambdaFile: string;
}

export class BedrockAgentCdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: BedrockAgentCdkProps) {
    super(scope, id, props);

    // Generate random number to avoid roles and lambda duplicates
    const randomPrefix = Math.floor(Math.random() * (10000 - 100) + 100);
    const apiKey = this.node.tryGetContext("apiKey") || API_KEY;
    const agentInstruction = this.node.tryGetContext("agentInstruction") || AGENT_INSTRUCTION;
    const agentName = this.node.tryGetContext("agentName") || AGENT_NAME;
    const agentModel = this.node.tryGetContext("agentModel") || AGENT_MODEL;
    const agentDescription = this.node.tryGetContext("apiKey") || AGENT_DESCRIPTION;
    
    // Travel Lambda configuration
    const travelLambdaName = `travel-agent-lambda-${randomPrefix}`;
    const travelLambdaRoleName = `travel-agent-lambda-role-${randomPrefix}`;
    
    // Portfolio Lambda configuration
    const portfolioLambdaName = `portfolio-agent-lambda-${randomPrefix}`;
    const portfolioLambdaRoleName = `portfolio-agent-lambda-role-${randomPrefix}`;
    
    const agentResourceRoleName = `AmazonBedrockExecutionRoleForAgents_${randomPrefix}`; 

    // Create IAM roles for both Lambdas
    const travelLambdaRole = new LambdaIamConstruct(this, `TravelLambdaIamConstruct-${randomPrefix}`, { 
      roleName: travelLambdaRoleName 
    });
    const portfolioLambdaRole = new LambdaIamConstruct(this, `PortfolioLambdaIamConstruct-${randomPrefix}`, { 
      roleName: portfolioLambdaRoleName 
    });

    // Create S3 bucket for schemas
    const s3Construct = new S3Construct(this, `agent-assets-${randomPrefix}`, {});

    // Create Bedrock agent role
    const bedrockAgentRole = new BedrockIamConstruct(this, `BedrockIamConstruct-${randomPrefix}`, { 
      roleName: agentResourceRoleName,
      lambdaRoleArn: `${travelLambdaRole.lambdaRole.roleArn},${portfolioLambdaRole.lambdaRole.roleArn}`,
      s3BucketArn: s3Construct.bucket.bucketArn,
    });
    bedrockAgentRole.node.addDependency(travelLambdaRole);
    bedrockAgentRole.node.addDependency(portfolioLambdaRole);
    bedrockAgentRole.node.addDependency(s3Construct);

    // Create Travel Lambda
    const travelLambdaConstruct = new LambdaConstruct(this, `TravelLambdaConstruct-${randomPrefix}`, {
      apiKey: apiKey,
      lambdaName: travelLambdaName,
      lambdaFile: props.travelLambdaFile,
      lambdaRoleName: travelLambdaRoleName,
      iamRole: travelLambdaRole.lambdaRole,
      dockerDirectory: 'lib/assets/lambda/travel'
    });
    travelLambdaConstruct.node.addDependency(travelLambdaRole);

    // Create Portfolio Lambda
    const portfolioLambdaConstruct = new LambdaConstruct(this, `PortfolioLambdaConstruct-${randomPrefix}`, {
      apiKey: apiKey,
      lambdaName: portfolioLambdaName,
      lambdaFile: props.portfolioLambdaFile,
      lambdaRoleName: portfolioLambdaRoleName,
      iamRole: portfolioLambdaRole.lambdaRole,
      environment: {
        STOCK_PORTFOLIO: process.env.STOCK_PORTFOLIO || '{}'
      },
      dockerDirectory: 'lib/assets/lambda/portfolio'
    });
    portfolioLambdaConstruct.node.addDependency(portfolioLambdaRole);

    // Create Bedrock agent with both action groups
    const bedrockAgentConstruct = new BedrockAgentConstruct(this, `BedrockConstruct-${randomPrefix}`, {
      apiKey: apiKey,
      agentName: agentName,
      agentModel: agentModel,
      agentInstruction: agentInstruction,
      agentDescription: agentDescription,
      agentRoleArn: bedrockAgentRole.roleArn,
      travelLambdaArn: travelLambdaConstruct.lambdaArn,
      portfolioLambdaArn: portfolioLambdaConstruct.lambdaArn,
      s3BucketName: s3Construct.bucketName
    });
    bedrockAgentConstruct.node.addDependency(bedrockAgentRole);
    bedrockAgentConstruct.node.addDependency(s3Construct);
    bedrockAgentConstruct.node.addDependency(travelLambdaConstruct);
    bedrockAgentConstruct.node.addDependency(portfolioLambdaConstruct);
  }
}
