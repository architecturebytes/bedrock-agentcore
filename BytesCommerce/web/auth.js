// Ensure that these values are correctly updated based on your Cognito User Pool setup
const cognitoConfig = {
    UserPoolId: 'us-east-1_GbolkuAxz',
    ClientId: 'cs9ddrljh6kif80pr7ohjfi5d',
    CognitoDomain: 'us-east-gbolkuaxz.auth.us-east-1.amazoncognito.com',
    RedirectUri: 'http://localhost:5001/callback.html'
};

// Redirect the user to the Cognito Hosted UI for login
function signIn() {
    const loginUrl = `https://${cognitoConfig.CognitoDomain}/login?response_type=code&client_id=${cognitoConfig.ClientId}&redirect_uri=${cognitoConfig.RedirectUri}`;
    window.location.assign(loginUrl);
}

// Handle the callback from Cognito after a successful login
async function handleCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');

    if (code) {
        try {
            const tokens = await exchangeCodeForTokens(code);
            localStorage.setItem('cognito_tokens', JSON.stringify(tokens));
            window.location.assign('/index.html'); // Redirect to the main chat page
        } catch (error) {
            console.error('Error exchanging code for tokens:', error);
            alert('Failed to log in. Please try again.');
            window.location.assign('/login.html');
        }
    }
}

// Exchange the authorization code for tokens
async function exchangeCodeForTokens(code) {
    const tokenUrl = `https://${cognitoConfig.CognitoDomain}/oauth2/token`;
    const params = new URLSearchParams();
    params.append('grant_type', 'authorization_code');
    params.append('client_id', cognitoConfig.ClientId);
    params.append('redirect_uri', cognitoConfig.RedirectUri);
    params.append('code', code);

    const response = await fetch(tokenUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: params
    });

    if (!response.ok) {
        throw new Error('Failed to exchange code for tokens');
    }

    return await response.json();
}

// Check if the user is logged in
function isLoggedIn() {
    return localStorage.getItem('cognito_tokens') !== null;
}

// Get the access token
function getAccessToken() {
    const tokens = JSON.parse(localStorage.getItem('cognito_tokens'));
    return tokens ? tokens.access_token : null;
}

// Sign the user out
function signOut() {
    localStorage.removeItem('cognito_tokens');
    const logoutRedirectUri = `${window.location.origin}/login.html`;
    const logoutUrl = `https://${cognitoConfig.CognitoDomain}/logout?client_id=${cognitoConfig.ClientId}&logout_uri=${encodeURIComponent(logoutRedirectUri)}`;
    window.location.assign(logoutUrl);
}
