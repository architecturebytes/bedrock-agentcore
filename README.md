# Bedrock AgentCore Tutorial

Ref YouTube Video: https://www.youtube.com/watch?v=W5byu-GsJ9A 

_BytesCommerce/BytesAgent.py_ <br>
Agent Code

_BytesCommerce/web_ <br>
Web Application

_BytesCommerce/tools/lambda/BytesCustomerSupportFunc.py_ <br>
Lambda Function (Tool)

_Policy (referred as BytesGWInvokePolicy in the video tutorial) to be added to Agent Execution Role:_ <br>
Make sure that Resource arn is correct as per your environment<br>
<pre>
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "InvokeBedrockAgentCoreGateway",
            "Effect": "Allow",
            "Action": "bedrock-agentcore:InvokeGateway",
            "Resource": "arn:aws:bedrock-agentcore:us-east-1:615820200535:gateway/bytesgateway-6h3ibq3k4z"
        }
    ]
}
</pre>
