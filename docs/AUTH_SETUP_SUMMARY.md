# API Authentication System - Implementation Summary

## ✅ What's Been Implemented

### 1. **Authentication Infrastructure**

#### JWT Verification (`src/app/auth/utils.py`)
- ✅ Supabase JWT token verification
- ✅ JWT token creation/encoding
- ✅ Authorization header parsing
- ✅ Error handling with proper HTTP status codes

#### FastAPI Dependencies (`src/app/auth/dependencies.py`)
- ✅ `get_current_user()` - Returns full JWT payload
- ✅ `get_current_user_id()` - Returns just user ID
- ✅ `get_current_user_email()` - Returns user email
- ✅ Type aliases for clean annotations: `CurrentUser`, `CurrentUserId`, `CurrentUserEmail`

#### Invite Code System (`src/app/auth/models.py`)
- ✅ `InviteCodeModel.create_invite()` - Generate new invite codes
- ✅ `InviteCodeModel.validate_invite()` - Check if code is valid/active
- ✅ `InviteCodeModel.use_invite()` - Mark code as used
- ✅ `InviteCodeModel.list_active_invites()` - Get unused codes
- ✅ `UserModel` - User profile management

### 2. **API Endpoints**

#### Public Endpoints (No Auth Required)

**`POST /auth/validate-invite`**
- Check if invite code is valid before showing signup form
- Frontend calls this to enable/disable signup button

**`POST /auth/register`**
- Create new user with invite code
- Returns JWT access token
- Requires: email, password, invite_code

**`POST /auth/login`**
- Login existing user
- Returns JWT access token
- Requires: email, password

#### Protected Endpoints (Requires JWT Token)

**`GET /auth/me`**
- Get current user profile
- Returns user details (id, email, role, domain_id, created_at)

**`POST /auth/logout`**
- Logout current user
- Clears session (client also clears token from localStorage)

#### Data API Endpoints (All Protected)
- ✅ `GET /api/v1/workflows` - List workflows
- ✅ `GET /api/v1/workflows/{id}` - Get workflow
- ✅ `POST /api/v1/workflows` - Create workflow
- ✅ `PUT /api/v1/workflows/{id}` - Update workflow
- ✅ `DELETE /api/v1/workflows/{id}` - Delete workflow
- ✅ `GET /api/v1/documents` - List documents
- ✅ `GET /api/v1/documents/{id}` - Get document
- ✅ `POST /api/v1/documents` - Create document
- ✅ `DELETE /api/v1/documents/{id}` - Delete document
- ✅ `GET /api/v1/domains` - List domains
- ✅ `GET /api/v1/domains/{id}` - Get domain
- ✅ `GET /api/v1/workflows/{id}/results` - Get workflow results

### 3. **Schemas**

#### Authentication Schemas (`src/app/schemas/auth.py`)
- ✅ `ValidateInviteRequest` - Invite code validation request
- ✅ `ValidateInviteResponse` - Validation response with domain/role
- ✅ `RegisterRequest` - User registration request
- ✅ `LoginRequest` - Login request
- ✅ `AuthResponse` - Token response
- ✅ `RefreshTokenRequest` - Token refresh request
- ✅ `UserProfileResponse` - User profile response

### 4. **Integration & Configuration**

#### Main API File (`service/api.py`)
- ✅ Auth routes included before data routes
- ✅ CORS configured for frontend domains
- ✅ Lifespan management for Temporal connection
- ✅ GraphQL integrated

#### Data Routes (`service/routes_data.py`)
- ✅ All endpoints protected with `CurrentUserId` dependency
- ✅ Documentation updated to show auth requirement

#### Auth Routes (`service/routes_auth.py`)
- ✅ Complete implementation of all auth endpoints
- ✅ Supabase integration for user management
- ✅ Proper error handling and logging

---

## 🚀 How It Works

### User Flow

```
1. User visits app
   ↓
2. Welcome page asks for invite code
   ↓
3. Frontend calls: POST /auth/validate-invite
   ↓
4. If valid, show signup form
   ↓
5. User enters email & password
   ↓
6. Frontend calls: POST /auth/register
   ↓
7. Backend:
   - Creates Supabase Auth user
   - Creates database user record
   - Marks invite code as used
   - Returns JWT token
   ↓
8. Frontend stores token in localStorage
   ↓
9. Frontend can now call protected endpoints
   ↓
10. All requests include: Authorization: Bearer <token>
```

### Technical Flow

```
Frontend Request
    ↓
Include Authorization header: Bearer <token>
    ↓
FastAPI receives request
    ↓
Route dependency: user_id: CurrentUserId
    ↓
get_current_user() is called
    ↓
extract_token_from_header() parses Authorization
    ↓
verify_supabase_jwt() validates token cryptographically
    ↓
Token valid? Yes → Proceed with endpoint
           No → Return 401 Unauthorized
    ↓
Endpoint executes with user_id available
```

---

## 📋 Database Schema Required

### Supabase Tables

#### `users` table
```sql
id (UUID, primary key)
email (text, unique)
role (text) - e.g., 'contributor', 'controller', 'admin'
domain_id (UUID, nullable)
created_at (timestamp)
```

#### `invite_codes` table
```sql
id (UUID, primary key)
code (text, unique) - e.g., 'ABC12345'
domain_id (UUID, nullable)
role (text) - role assigned when code is used
created_by (UUID, nullable) - admin who created it
used_by (UUID, nullable) - user who used it
used_at (timestamp, nullable)
expires_at (timestamp) - when code expires
created_at (timestamp)
```

**Note:** These tables must exist in Supabase for the system to work.

---

## 🔑 Environment Variables

Set these in your `.env` file:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret

# Temporal
TEMPORAL_ADDRESS=localhost:7233
TEMPORAL_NAMESPACE=default

# Other
LOG_LEVEL=INFO
```

---

## 📖 Documentation Files

### `AUTH_INTEGRATION_GUIDE.md`
Complete guide for frontend developers:
- Welcome page implementation
- Signup page implementation
- Login page implementation
- API wrapper for authenticated requests
- All API endpoints with examples
- cURL testing examples
- Error handling
- Security best practices

### `test_auth_flow.sh`
Automated test script that:
1. Validates invite code
2. Checks API health
3. Tests protected endpoint without token (should fail)
4. Registers new user
5. Gets user profile with token
6. Lists documents with token
7. Tests logout

**Run with:**
```bash
./test_auth_flow.sh
```

---

## 🧪 Testing

### Manual Testing with cURL

**Validate Invite:**
```bash
curl -X POST http://localhost:8000/auth/validate-invite \
  -H "Content-Type: application/json" \
  -d '{"code":"TEST-12345"}'
```

**Register:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "password":"password123",
    "invite_code":"TEST-12345"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "password":"password123"
  }'
```

**Protected Request:**
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Automated Testing
```bash
cd /Users/kpernyer/repo/hey-sh-workflow/backend
./test_auth_flow.sh
```

---

## 🔐 Security Features

✅ **JWT Verification**
- Cryptographic verification using Supabase secret
- Token expiration checking
- User ID validation

✅ **Password Security**
- Managed by Supabase Auth (bcrypt hashing)
- Minimum 8 characters enforced
- Never stored in database

✅ **Invite Code Protection**
- One-time use enforcement
- Expiration enforcement
- Domain/role restrictions possible

✅ **API Protection**
- All data endpoints require valid token
- 401 Unauthorized for missing/invalid tokens
- Proper CORS configuration

✅ **Error Handling**
- Doesn't leak sensitive information
- Consistent error responses
- Proper HTTP status codes

---

## 📦 File Structure

```
backend/
├── src/app/auth/
│   ├── __init__.py
│   ├── utils.py          ← JWT verification & token handling
│   ├── dependencies.py   ← FastAPI dependency injection
│   └── models.py         ← Invite codes & user management
├── src/app/schemas/
│   └── auth.py           ← Request/response schemas
├── service/
│   ├── api.py            ← Main FastAPI app (UPDATED)
│   ├── routes_auth.py    ← Auth endpoints (NEW)
│   └── routes_data.py    ← Data endpoints (UPDATED with auth)
├── AUTH_INTEGRATION_GUIDE.md      ← Frontend guide (NEW)
├── AUTH_SETUP_SUMMARY.md          ← This file
└── test_auth_flow.sh              ← Test script (NEW)
```

---

## 🔄 Next Steps

### 1. Setup Supabase
- [ ] Create `users` and `invite_codes` tables
- [ ] Enable Row Level Security (optional but recommended)
- [ ] Get your SUPABASE_URL, SUPABASE_KEY, SUPABASE_JWT_SECRET

### 2. Generate Invite Codes
- [ ] Create admin CLI tool: `tool/generate_invites.py`
- [ ] Generate beta testing codes

### 3. Frontend Integration
- [ ] Copy code from AUTH_INTEGRATION_GUIDE.md
- [ ] Create Welcome page (invite code input)
- [ ] Create Signup page
- [ ] Create Login page
- [ ] Create API wrapper with auth header
- [ ] Update all API calls to use wrapper

### 4. Testing
- [ ] Run `./test_auth_flow.sh`
- [ ] Manual cURL testing
- [ ] Full end-to-end with frontend

### 5. Deployment
- [ ] Configure CORS for production domain
- [ ] Set environment variables in deployment
- [ ] Enable HTTPS
- [ ] Configure rate limiting (optional)

---

## 🐛 Troubleshooting

### "Invalid token"
- Token may be expired (1 hour TTL)
- Re-login or use refresh endpoint
- Check SUPABASE_JWT_SECRET matches Supabase project

### "Invalid invite code"
- Code may have already been used
- Code may have expired (30 days default)
- Code doesn't exist

### "401 Unauthorized"
- Check Authorization header format: `Bearer <token>`
- Make sure token is included
- Token may be malformed

### Database Connection Issues
- Verify SUPABASE_URL and SUPABASE_KEY
- Check that tables exist in Supabase
- Test connection with Supabase CLI

---

## 📞 Support

For issues:
1. Check the troubleshooting section above
2. Review AUTH_INTEGRATION_GUIDE.md
3. Run test_auth_flow.sh to debug
4. Check backend logs: `docker-compose logs -f backend`

---

## 🎯 Success Criteria

You'll know it's working when:

✅ `./test_auth_flow.sh` passes all tests
✅ Frontend can validate invite codes
✅ New users can register with invite code
✅ Users can login with email/password
✅ Protected API endpoints return data with valid token
✅ Protected API endpoints return 401 without token
✅ User profile endpoint returns user details
✅ Logout clears token
✅ Token expiration works correctly
