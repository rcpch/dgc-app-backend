import * as client from 'openid-client';

const config = await client.discovery(
  new URL(import.meta.env.VITE_DEMO_OAUTH_SERVER),
  import.meta.env.VITE_DEMO_OAUTH_CLIENT_ID,
  {
    client_secret: import.meta.env.VITE_DEMO_OAUTH_CLIENT_SECRET,
  }
);

const loginForm = document.getElementById('login_form')!;
const subDisplay = document.getElementById('sub')!;
const testForm = document.getElementById('test_form')!;

const token = localStorage['access_token'];

async function login() {
  const code_verifier = client.randomPKCECodeVerifier();
    const code_challenge = await client.calculatePKCECodeChallenge(code_verifier);

    const state = client.randomState();

    const parameters = {
      redirect_uri: 'https://dgc-app-backend.localhost/demo/oauth-callback',
      scope: 'openid profile email',
      code_challenge,
      code_challenge_method: 'S256',
      state
    }

    const authUrl = client.buildAuthorizationUrl(config, parameters);

    sessionStorage['code_verifier'] = code_verifier;
    sessionStorage['state'] = state;

    window.location.href = authUrl.href;
}

async function testBackend() {
  const response = await fetch("/api/hello", {
    headers: {
      'Authorization': `Bearer ${localStorage['access_token']}`
    }
  });

  console.log(response.status)
}

testForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  await testBackend();
});

if (token) {
  testForm.style.display = "block";
  subDisplay.textContent = `Logged in as: ${JSON.parse(atob(token.split('.')[1])).sub}`;

  loginForm.querySelector("input[type=submit]")!.setAttribute("value", "Logout");

  loginForm.onsubmit = async (e) => {
    e.preventDefault();
    
    delete localStorage['access_token'];

    testForm.style.display = "none";
    subDisplay.textContent = "";

    loginForm.querySelector("input[type=submit]")?.setAttribute("value", "Login");

    loginForm.onsubmit = async (e) => {
      e.preventDefault(); 
      await login();
    }
  }
} else {
  loginForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    await login();
  });
}