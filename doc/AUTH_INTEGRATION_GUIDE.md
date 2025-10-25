# API Authentication & Authorization Guide

This document explains how to integrate with the Hey.sh Backend API authentication system.

## Overview

The API uses:
- **Supabase Auth** for user accounts
- **JWT tokens** (Bearer tokens) for request authentication
- **Invite codes** for beta access control
- **Role-based access** (contributor, controller, admin)

## Frontend Integration Flow

### 1. Welcome Page - Invite Code Input

User lands on app → sees welcome page with invite code input

```javascript
// frontend/src/pages/Welcome.jsx
import { useState } from 'react';

export default function WelcomePage() {
  const [inviteCode, setInviteCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleValidateInvite = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/auth/validate-invite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: inviteCode }),
      });

      if (!response.ok) {
        setError('Invalid invite code');
        setLoading(false);
        return;
      }

      const data = await response.json();

      if (data.valid) {
        // Show signup form
        localStorage.setItem('pendingInviteCode', inviteCode);
        window.location.href = '/signup';
      } else {
        setError(data.message || 'Invalid invite code');
      }
    } catch (err) {
      setError('Failed to validate invite code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="welcome-container">
      <h1>Welcome to Hey.sh</h1>
      <p>Enter your beta invite code to get started</p>

      <input
        type="text"
        placeholder="Enter invite code"
        value={inviteCode}
        onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
        disabled={loading}
      />

      <button onClick={handleValidateInvite} disabled={loading}>
        {loading ? 'Validating...' : 'Continue'}
      </button>

      {error && <p className="error">{error}</p>}
    </div>
  );
}
```

### 2. Signup Page - Create Account

```javascript
// frontend/src/pages/Signup.jsx
import { useState } from 'react';

export default function SignupPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const inviteCode = localStorage.getItem('pendingInviteCode');
    if (!inviteCode) {
      setError('No invite code found. Please start over.');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          password,
          invite_code: inviteCode,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        setError(errorData.detail || 'Signup failed');
        setLoading(false);
        return;
      }

      const data = await response.json();

      // Store token
      localStorage.setItem('authToken', data.access_token);
      localStorage.setItem('userId', data.user_id);
      localStorage.removeItem('pendingInviteCode');

      // Redirect to app
      window.location.href = '/app';
    } catch (err) {
      setError('Signup failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSignup}>
      <h2>Create Your Account</h2>

      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />

      <input
        type="password"
        placeholder="Password (min 8 characters)"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        minLength={8}
        required
      />

      <button type="submit" disabled={loading}>
        {loading ? 'Creating account...' : 'Sign Up'}
      </button>

      {error && <p className="error">{error}</p>}
    </form>
  );
}
```

### 3. Login Page - Returning Users

```javascript
// frontend/src/pages/Login.jsx
import { useState } from 'react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        setError('Invalid email or password');
        setLoading(false);
        return;
      }

      const data = await response.json();

      // Store tokens
      localStorage.setItem('authToken', data.access_token);
      localStorage.setItem('userId', data.user_id);

      // Redirect to app
      window.location.href = '/app';
    } catch (err) {
      setError('Login failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <h2>Login</h2>

      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />

      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>

      {error && <p className="error">{error}</p>}
    </form>
  );
}
```

### 4. Authenticated API Requests

**Create a reusable fetch wrapper:**

```javascript
// frontend/src/lib/api.js
export async function apiCall(endpoint, options = {}) {
  const token = localStorage.getItem('authToken');

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`http://localhost:8000${endpoint}`, {
    ...options,
    headers,
  });

  // Handle token expiration
  if (response.status === 401) {
    // Token expired, redirect to login
    localStorage.removeItem('authToken');
    localStorage.removeItem('userId');
    window.location.href = '/login';
    return;
  }

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}
```

**Use it in your components:**

```javascript
// frontend/src/components/Documents.jsx
import { useEffect, useState } from 'react';
import { apiCall } from '../lib/api';

export default function DocumentsList() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const data = await apiCall('/api/v1/documents');
        setDocuments(data.documents);
      } catch (err) {
        setError('Failed to load documents: ' + err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
  }, []);

  if (loading) return <p>Loading...</p>;
  if (error) return <p className="error">{error}</p>;

  return (
    <div>
      <h2>Documents ({documents.length})</h2>
      <ul>
        {documents.map((doc) => (
          <li key={doc.id}>{doc.name}</li>
        ))}
      </ul>
    </div>
  );
}
```

## API Endpoints

### Public Endpoints (No Auth Required)

#### Validate Invite Code
```bash
POST /auth/validate-invite
Content-Type: application/json

{
  "code": "ABC12345"
}

# Response
{
  "valid": true,
  "message": "Invite code is valid",
  "domain_id": "domain-uuid",
  "role": "contributor"
}
```

#### Register with Invite Code
```bash
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure-password-8-chars-min",
  "invite_code": "ABC12345"
}

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": "user-uuid",
  "email": "user@example.com"
}
```

#### Login
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure-password"
}

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": "user-uuid",
  "email": "user@example.com"
}
```

### Protected Endpoints (Requires JWT Token)

All protected endpoints require:
```
Authorization: Bearer <access_token>
```

#### Get Current User Profile
```bash
GET /auth/me
Authorization: Bearer <token>

# Response
{
  "id": "user-uuid",
  "email": "user@example.com",
  "role": "contributor",
  "domain_id": "domain-uuid",
  "created_at": "2024-10-19T12:00:00Z"
}
```

#### List Workflows
```bash
GET /api/v1/workflows?domain_id=domain-uuid
Authorization: Bearer <token>

# Response
{
  "workflows": [...],
  "count": 5
}
```

#### List Documents
```bash
GET /api/v1/documents?domain_id=domain-uuid
Authorization: Bearer <token>

# Response
{
  "documents": [...],
  "count": 10
}
```

#### Create Workflow
```bash
POST /api/v1/workflows
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "My Workflow",
  "domain_id": "domain-uuid",
  "yaml_definition": {...},
  "description": "Optional description"
}
```

#### Logout
```bash
POST /auth/logout
Authorization: Bearer <token>

# Response
{
  "message": "Successfully logged out"
}
```

## Token Management

### Token Expiration
- Access tokens expire after 1 hour (default)
- When you get a 401 response, the token has expired
- Clear token and redirect to login

### Token Refresh (If Implemented)
```javascript
// This is optional - for now, just re-login
async function refreshToken() {
  const response = await fetch('http://localhost:8000/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      refresh_token: localStorage.getItem('refreshToken')
    }),
  });

  const data = await response.json();
  localStorage.setItem('authToken', data.access_token);
  return data.access_token;
}
```

## Error Handling

All errors return a consistent format:

```json
{
  "detail": "Error message here"
}
```

Common status codes:
- **200** - Success
- **201** - Created
- **400** - Bad request (invalid input)
- **401** - Unauthorized (missing/invalid token)
- **404** - Not found
- **500** - Server error

## Testing with cURL

### Validate Invite
```bash
curl -X POST http://localhost:8000/auth/validate-invite \
  -H "Content-Type: application/json" \
  -d '{"code":"ABC12345"}'
```

### Register
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "password":"securepass123",
    "invite_code":"ABC12345"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "password":"securepass123"
  }'
```

### Protected Request (Replace TOKEN)
```bash
curl -X GET http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer TOKEN"
```

### Get Current User
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer TOKEN"
```

## Environment Variables

Set these in your `.env` file:

```bash
# Backend
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
SUPABASE_JWT_SECRET=your-jwt-secret

# Frontend
VITE_API_URL=http://localhost:8000
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR NOT NULL UNIQUE,
  role VARCHAR DEFAULT 'contributor',
  domain_id UUID,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Invite Codes Table
```sql
CREATE TABLE invite_codes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code VARCHAR UNIQUE NOT NULL,
  domain_id UUID,
  role VARCHAR DEFAULT 'contributor',
  created_by UUID,
  used_by UUID,
  used_at TIMESTAMP,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Next Steps

1. **Frontend Setup**: Copy the code snippets above into your React/Vue/etc app
2. **Test Authentication**: Use cURL commands to test each endpoint
3. **Generate Invites**: Create invite codes (see Admin Guide below)
4. **User Testing**: Have beta testers use the invite code to sign up

## Admin Guide - Generating Invite Codes

*(To be implemented as CLI tool)*

```bash
# Create 100 invite codes for beta testing
uv run tool/generate_invites.py \
  --count 100 \
  --domain-id optional-domain-uuid \
  --expires-days 30 \
  --role contributor

# Create admin-level invites
uv run tool/generate_invites.py \
  --count 10 \
  --role admin \
  --expires-days 90
```

## Troubleshooting

**Issue: "Invalid or expired invite code"**
- Check that the code wasn't already used
- Check that the code hasn't expired
- Ensure the code format is correct

**Issue: "Missing Authorization header"**
- Make sure you're including the Bearer token
- Format: `Authorization: Bearer <token>`

**Issue: 401 Unauthorized**
- Token may be expired, re-login
- Token might be malformed, check localStorage
- Check SUPABASE_JWT_SECRET is set correctly

**Issue: CORS errors**
- Ensure frontend origin is in CORS_ORIGINS in api.py
- Add your domain if deploying to production

## Security Best Practices

✅ **DO:**
- Store tokens in localStorage or sessionStorage (not cookies unless httpOnly)
- Always use HTTPS in production
- Validate invite codes before showing signup form
- Clear tokens on logout
- Use strong passwords (8+ chars, mixed case, numbers, symbols)

❌ **DON'T:**
- Store tokens in plain text files
- Expose JWT secrets in frontend code
- Share invite codes publicly
- Use same password for multiple accounts
- Commit .env files with secrets to git

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review API endpoint documentation
3. Check backend logs: `docker-compose logs -f backend`
4. Test with cURL before debugging frontend code
