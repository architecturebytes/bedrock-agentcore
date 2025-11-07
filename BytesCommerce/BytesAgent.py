import os
import json
import sys
from strands import Agent, tool
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from bedrock_agentcore.tools.code_interpreter_client import CodeInterpreter
from bedrock_agentcore.runtime import BedrockAgentCoreApp

from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client, StreamableHTTPTransport
from botocore.session import Session
from botocore.credentials import Credentials
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import httpx
from typing import Generator
from datetime import timedelta

app = BedrockAgentCoreApp()

MEMORY_ID = os.getenv("BEDROCK_AGENTCORE_MEMORY_ID")
REGION = os.getenv("AWS_REGION")

# NOTE: Update these values as required.

# Bedrock LLM Model Id
MODEL_ID = "amazon.nova-micro-v1:0"

# (AgentCore) Gateway URL (if not set in environment, it will pick up from here)
GATEWAY_URL = os.getenv("GATEWAY_URL", "https://bytesgateway-6h3ibq3k4z.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp")

# Gateway Region - (if not set in environment, it will pick up from here)
GATEWAY_REGION = os.getenv("GATEWAY_REGION", "us-east-1")

SYSTEM_PROMPT = "You are a helpful assistant. Use tools when appropriate."

class SigV4HTTPXAuth(httpx.Auth):
    """HTTPX Auth class that signs requests with AWS SigV4."""

    def __init__(
        self,
        credentials: Credentials,
        service: str,
        region: str,
    ):
        self.credentials = credentials
        self.service = service
        self.region = region
        self.signer = SigV4Auth(credentials, service, region)

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        """Signs the request with SigV4 and adds the signature to the request headers."""

        headers = dict(request.headers)
        headers.pop("connection", None)

        aws_request = AWSRequest(
            method=request.method,
            url=str(request.url),
            data=request.content,
            headers=headers,
        )

        self.signer.add_auth(aws_request)

        request.headers.update(dict(aws_request.headers))

        yield request


def get_full_tools_list(client):
    """Get all tools with pagination support"""
    more_tools = True
    tools = []
    pagination_token = None
    while more_tools:
        tmp_tools = client.list_tools_sync(pagination_token=pagination_token)
        tools.extend(tmp_tools)
        if tmp_tools.pagination_token is None:
            more_tools = False
        else:
            more_tools = True
            pagination_token = tmp_tools.pagination_token
    return tools

@app.entrypoint
def invoke(payload, context):


    if not MEMORY_ID:
        return {"error": "Memory not configured"}
    if not REGION:
        return {"error": "AWS_REGION not configured"}

    actor_id = context.headers.get('X-Amzn-Bedrock-AgentCore-Runtime-Custom-Actor-Id', 'user') if hasattr(context, 'headers') else 'user'
    session_id = None
    if hasattr(context, 'headers') and 'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id' in context.headers:
        session_id = context.headers.get('X-Amzn-Bedrock-AgentCore-Runtime-Session-Id')
    elif payload and 'session_id' in payload:
        session_id = payload.get('session_id')
    else:
        session_id = 'default'

    # Setup MCP client for IAM authentication.
    credentials = Session().get_credentials()
    auth = SigV4HTTPXAuth(credentials, "bedrock-agentcore", GATEWAY_REGION)
    transport_factory = lambda: streamablehttp_client(url=GATEWAY_URL, auth=auth)
    mcp_client = MCPClient(transport_factory)

    # List available tools from Gateway
    gateway_tools = []
    with mcp_client:
        try:
            gateway_tools = get_full_tools_list(mcp_client)
            print(f"Successfully loaded {len(gateway_tools)} tools from Gateway.")
        except Exception as e:
            print(f"Error loading tools from Gateway: {e}")
            pass # Proceed without gateway tools if there's an error

        actor_id = context.headers.get('X-Amzn-Bedrock-AgentCore-Runtime-Custom-Actor-Id', 'user') if hasattr(context, 'headers') else 'user'
        
        # Attempt to get session_id from context headers first, then from payload, otherwise default to 'default'
        session_id = None
        if hasattr(context, 'headers') and 'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id' in context.headers:
            session_id = context.headers.get('X-Amzn-Bedrock-AgentCore-Runtime-Session-Id')
        elif payload and 'session_id' in payload:
            session_id = payload.get('session_id')
        else:
            session_id = 'default'

        memory_config = AgentCoreMemoryConfig(
            memory_id=MEMORY_ID,
            session_id=session_id,
            actor_id=actor_id,
            retrieval_config={
                f"/users/{actor_id}/facts": RetrievalConfig(top_k=3, relevance_score=0.5),
                f"/users/{actor_id}/preferences": RetrievalConfig(top_k=3, relevance_score=0.5)
            }
        )

        all_tools = gateway_tools

        bedrockmodel = BedrockModel(
            model_id=MODEL_ID,
            streaming=True,
        )

        agent = Agent(
            model=bedrockmodel,
            tools=all_tools,
            session_manager=AgentCoreMemorySessionManager(memory_config, REGION), # Reintroduced session_manager
            system_prompt=SYSTEM_PROMPT
        )

        prompt_text = ""
        # Prioritize the script.js payload structure
        if "payload" in payload:
            inner_payload_str = payload.get("payload", "{}")
            try:
                inner_payload = json.loads(inner_payload_str)
                prompt_text = inner_payload.get("prompt", "")
            except json.JSONDecodeError:
                # If it's not valid JSON, treat it as an empty prompt
                prompt_text = ""
        elif "prompt" in payload:
            # Fallback to direct prompt in the top-level payload (for existing clients)
            prompt_text = payload.get("prompt", "")
        # If neither case matches, prompt_text remains an empty string, which will be handled by the agent.

        # print(f"DEBUG: Extracted prompt_text: {prompt_text}") # Removed for debugging

        result = agent(prompt_text)
        return {"response": result.message.get('content', [{}])[0].get('text', str(result))}

if __name__ == "__main__":
    app.run()
