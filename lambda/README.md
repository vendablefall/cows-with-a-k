# Cows with a K - Lambda Functions

AWS Lambda functions for the authentication API.

## Functions

### 1. signin.py
Handles user authentication and JWT token generation.

**Endpoint:** `POST /auth/signin`

**Environment Variables:**
- `USERS_TABLE`: DynamoDB table name for users (default: CowsWithAK-Users)
- `JWT_SECRET`: Secret key for JWT token signing
- `JWT_ALGORITHM`: Algorithm for JWT (default: HS256)

### 2. signup.py
Handles new user registration with council approval system.

**Endpoint:** `POST /auth/signup`

**Environment Variables:**
- `USERS_TABLE`: DynamoDB table name for users
- `ADMIN_EMAIL`: Email address for admin notifications
- `SES_SENDER`: SES verified sender email

### 3. signout.py
Invalidates JWT tokens by adding them to a blacklist.

**Endpoint:** `POST /auth/signout`

**Environment Variables:**
- `BLACKLIST_TABLE`: DynamoDB table for token blacklist (default: CowsWithAK-TokenBlacklist)
- `JWT_SECRET`: Secret key for JWT token verification

### 4. get_current_user.py
Returns information about the currently authenticated user.

**Endpoint:** `GET /auth/me`

**Environment Variables:**
- `USERS_TABLE`: DynamoDB table name for users
- `BLACKLIST_TABLE`: DynamoDB table for token blacklist
- `JWT_SECRET`: Secret key for JWT token verification

### 5. get_messages.py
Retrieves paginated messages from the message board.

**Endpoint:** `GET /messages`

**Environment Variables:**
- `MESSAGES_TABLE`: DynamoDB table for messages (default: CowsWithAK-Messages)
- `BLACKLIST_TABLE`: DynamoDB table for token blacklist
- `JWT_SECRET`: Secret key for JWT token verification

### 6. post_message.py
Posts a new message to the message board.

**Endpoint:** `POST /messages`

**Environment Variables:**
- `MESSAGES_TABLE`: DynamoDB table for messages
- `USERS_TABLE`: DynamoDB table name for users
- `BLACKLIST_TABLE`: DynamoDB table for token blacklist
- `JWT_SECRET`: Secret key for JWT token verification

### 7. delete_message.py
Deletes a message from the board (owner or admin only).

**Endpoint:** `DELETE /messages/{messageId}`

**Environment Variables:**
- `MESSAGES_TABLE`: DynamoDB table for messages
- `USERS_TABLE`: DynamoDB table name for users
- `BLACKLIST_TABLE`: DynamoDB table for token blacklist
- `JWT_SECRET`: Secret key for JWT token verification

## DynamoDB Tables

### Users Table (CowsWithAK-Users)
```
Primary Key: email (String)

Attributes:
- userId (String)
- email (String)
- username (String)
- firstName (String) - User's first name
- lastName (String) - User's last name
- cowName (String) - User's cow/paddock name
- profilePicture (String) - Base64 encoded profile picture (optional)
- profilePictureName (String) - Original filename of profile picture (optional)
- profilePictureType (String) - MIME type of profile picture (optional)
- passwordHash (String)
- passwordSalt (String)
- status (String): pending, active, suspended
- clearanceLevel (String): LEVEL 1, LEVEL 2, TOP SECRET
- answers (Map) - Security question answers
- createdAt (String - ISO 8601)
- lastLogin (String - ISO 8601)
```

### Token Blacklist Table (CowsWithAK-TokenBlacklist)
```
Primary Key: token (String)

Attributes:
- token (String)
- blacklistedAt (String - ISO 8601)
- ttl (Number) - DynamoDB TTL for auto-deletion
```

### Messages Table (CowsWithAK-Messages)
```
Primary Key: messageId (String)

Attributes:
- messageId (String)
- userId (String)
- username (String)
- content (String)
- timestamp (String - ISO 8601)
- clearanceLevel (String)

GSI: timestamp-index (for chronological retrieval)
- Partition Key: timestamp (String)
```

## Deployment

### 1. Install Dependencies
```bash
cd lambda
pip install -r requirements.txt -t .
```

### 2. Create Deployment Package
```bash
# For each function
zip -r signin.zip signin.py
zip -r signup.zip signup.py
zip -r signout.zip signout.zip
zip -r get_current_user.zip get_current_user.py

# Include dependencies
zip -r -g signin.zip jwt/ cryptography/ ...
```

### 3. Create Lambda Functions in AWS Console
- Runtime: Python 3.11
- Handler: `signin.lambda_handler` (adjust for each function)
- Memory: 256 MB
- Timeout: 30 seconds

### 4. Set Environment Variables
Configure the environment variables for each function as listed above.

### 5. Create API Gateway
1. Create a REST API
2. Create resources matching the OpenAPI spec
3. Create methods (POST, GET) for each resource
4. Set up Lambda integrations
5. Enable CORS
6. Deploy to stage (prod/dev)

### 6. IAM Permissions
Ensure Lambda execution role has:
- DynamoDB: GetItem, PutItem, UpdateItem, Query
- SES: SendEmail (for signup function)
- CloudWatch Logs: CreateLogGroup, CreateLogStream, PutLogEvents

## Testing

### Test Sign Up
```bash
curl -X POST https://your-api.execute-api.region.amazonaws.com/prod/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@cow.com",
    "password": "TestMoo123",
    "answers": {
      "q1": "Kentucky Bluegrass",
      "q2": "Four (Correct)",
      "q3": "divine",
      "q4": "Grazing all day long"
    }
  }'
```

### Test Sign In
```bash
curl -X POST https://your-api.execute-api.region.amazonaws.com/prod/auth/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@cow.com",
    "password": "moo"
  }'
```

### Test Get Current User
```bash
curl -X GET https://your-api.execute-api.region.amazonaws.com/prod/auth/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Test Sign Out
```bash
curl -X POST https://your-api.execute-api.region.amazonaws.com/prod/auth/signout \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Security Considerations

1. **JWT Secret**: Use AWS Secrets Manager or Parameter Store in production
2. **HTTPS Only**: Enforce HTTPS in API Gateway
3. **Rate Limiting**: Configure API Gateway throttling
4. **Password Complexity**: Current validation requires 8+ chars with mixed case and digits
5. **Token Expiry**: Default 24 hours, adjust as needed
6. **CORS**: Configure specific origins in production, not `*`

## Monitoring

- CloudWatch Logs for function execution
- API Gateway metrics for request/error rates
- DynamoDB metrics for read/write capacity
- Set up CloudWatch Alarms for errors

## Future Enhancements

- Password reset functionality
- Email verification
- Multi-factor authentication
- Refresh token rotation
- Rate limiting per user
- Session management
