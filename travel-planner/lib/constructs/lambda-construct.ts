import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as logs from 'aws-cdk-lib/aws-logs';

export interface LambdaProps extends cdk.StackProps {
  readonly apiKey: string;
  readonly lambdaRoleName: string;
  readonly lambdaFile: string;
  readonly lambdaName: string;
  readonly iamRole: cdk.aws_iam.Role;
  readonly environment?: { [key: string]: string };
  readonly dockerDirectory: string;  // Path to the Docker context directory
}

const defaultProps: Partial<LambdaProps> = {};

export class LambdaConstruct extends Construct {
  public lambdaArn: string;
  public logGroupName: string;

  constructor(scope: Construct, name: string, props: LambdaProps) {
    super(scope, name);

    props = { ...defaultProps, ...props };

    // Create CloudWatch Log Group with 30-day retention
    const logGroup = new logs.LogGroup(this, `${props.lambdaName}-logs`, {
      logGroupName: `/aws/lambda/${props.lambdaName}`,
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY
    });

    // Create Lambda function
    const lambda = new cdk.aws_lambda.DockerImageFunction(this, props.lambdaName, {
      code: cdk.aws_lambda.DockerImageCode.fromImageAsset(props.dockerDirectory),
      timeout: cdk.Duration.seconds(300),
      role: props.iamRole,
      functionName: props.lambdaName,
      environment: {
        API_KEY: props.apiKey,
        ...props.environment,
      },
      logGroup,
    });

    // Grant Bedrock invoke permissions
    lambda.grantInvoke(new cdk.aws_iam.ServicePrincipal("bedrock.amazonaws.com"));

    // Store outputs
    this.lambdaArn = lambda.functionArn;
    this.logGroupName = logGroup.logGroupName;

    // Create CloudFormation outputs
    new cdk.CfnOutput(this, `${props.lambdaName}Arn`, {
      value: lambda.functionArn,
      description: `ARN for ${props.lambdaName}`
    });

    new cdk.CfnOutput(this, `${props.lambdaName}LogGroup`, {
      value: logGroup.logGroupName,
      description: `CloudWatch Log Group for ${props.lambdaName}`
    });
  }
}