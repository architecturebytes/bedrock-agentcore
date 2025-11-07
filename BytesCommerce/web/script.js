const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');

// NOTE: Update Agent ARN 
const AGENT_RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:615820200535:runtime/BytesAgent-O0AgrtENxc";

const encodedArn = encodeURIComponent(AGENT_RUNTIME_ARN);
const AGENT_URL = "https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/" + encodedArn + "/invocations";

SESSION_ID = "dfmeoagmreaklgnrkleafremojgrmtesogmtrskhmtkrmshmv";

userInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    event.preventDefault();
    sendMessage();
  }
});

sendButton.addEventListener('click', sendMessage);

async function sendMessage() {
  const userMessage = userInput.value;
  if (userMessage.trim() === '') {
    return;
  }

  appendMessage(userMessage, 'user-message');
  userInput.value = '';

  try {
    const accessToken = getAccessToken();
    if (!accessToken) {
      alert('You are not logged in. Please log in again.');
      signOut();
      return;
    }

    const agentResponse = await invokeBedrockAgent(userMessage, accessToken);
    appendMessage(agentResponse, 'agent-message');

  } catch (error) {
    console.error('Error:', error);
    appendMessage('Error: Could not connect to the agent.', 'agent-message');
  }
}

async function invokeBedrockAgent(message, token) {
	
    const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
    };

    const payload = {
        "agentRuntimeArn": AGENT_RUNTIME_ARN,
        "session_id": SESSION_ID,
        "payload": JSON.stringify({ "prompt": message }),
        "qualifier": "DEFAULT"
    };

    const response = await fetch(AGENT_URL, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        let errorBody = '';
        const responseText = await response.text(); // Read the body once as text
        try {
            const errorData = JSON.parse(responseText); // Try to parse the text as JSON
            errorBody = JSON.stringify(errorData);
        } catch (e) {
            errorBody = responseText; // If not JSON, use the raw text
        }
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorBody}`);
    }

    const responseData = await response.json();
    // The response from the direct HTTPS API call might be different.
    // We will need to inspect it to get the actual message.
    // For now, we'll assume it's in a similar format as before.
    return responseData.response || JSON.stringify(responseData);
}

function appendMessage(message, className) {
  const messageElement = document.createElement('div');
  messageElement.classList.add('message', className);

  if (message.includes('<thinking>')) {
    const thinkingPart = message.match(/<thinking>[\s\S]*?<\/thinking>/)[0];
    const restOfMessage = message.replace(thinkingPart, '').trim();
    const escapedThinkingPart = thinkingPart.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    messageElement.innerHTML = `<span class="thinking-text">${escapedThinkingPart}</span><br>${restOfMessage}`;
  } else {
    messageElement.textContent = message;
  }

  chatContainer.appendChild(messageElement);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}
