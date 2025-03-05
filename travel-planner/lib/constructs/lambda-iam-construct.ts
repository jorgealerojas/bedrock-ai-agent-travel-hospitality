import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";

export interface LambdaIamProps extends cdk.StackProps {
  readonly roleName: string;
}

const defaultProps: Partial<LambdaIamProps> = {};

export class LambdaIamConstruct extends Construct {
  public lambdaRole: cdk.aws_iam.Role;

  constructor(scope: Construct, name: string, props: LambdaIamProps) {
    super(scope, name);

    props = { ...defaultProps, ...props };

    this.lambdaRole = new cdk.aws_iam.Role(this, "LambdaRole", {
      roleName: props.roleName,
      assumedBy: new cdk.aws_iam.ServicePrincipal("lambda.amazonaws.com"),
    });

    // Add CloudWatch Logs permissions
    this.lambdaRole.addToPolicy(
      new cdk.aws_iam.PolicyStatement({
        effect: cdk.aws_iam.Effect.ALLOW,
        actions: [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ],
        resources: ["arn:aws:logs:*:*:*"]
      })
    );

    // Add existing SerpAPI permissions
    this.lambdaRole.addToPolicy(
      new cdk.aws_iam.PolicyStatement({
        effect: cdk.aws_iam.Effect.ALLOW,
        actions: ["bedrock:*"],
        resources: ["*"],
      })
    );

    new cdk.CfnOutput(this, "LambdaRoleArn", {
      value: this.lambdaRole.roleArn,
    });
  }
}