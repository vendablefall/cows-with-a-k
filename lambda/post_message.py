"""
AWS Lambda function to post messages to the message board
Creates new messages in DynamoDB
"""

import json
import boto3
import os
from datetime import datetime
import uuid
import jwt

# AWS Clients
dynamodb = boto3.resource('dynamodb')
messages_table = dynamodb.Table(os.environ.get('MESSAGES_TABLE', 'CowsWithAK-Messages'))
users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'CowsWithAK-Users'))
blacklist_table = dynamodb.Table(os.environ.get('BLACKLIST_TABLE', 'CowsWithAK-TokenBlacklist'))

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'moo-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'


def verify_token(token):
    """Verify JWT token and extract payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, {'error': 'Token has expired'}
    except jwt.InvalidTokenError:
        return False, {'error': 'Invalid token'}


def is_token_blacklisted(token):
    """Check if token is in blacklist"""
    try:
        response = blacklist_table.get_item(Key={'token': token})
        return 'Item' in response
    except Exception as e:
        print(f"Error checking blacklist: {str(e)}")
        return False


def extract_token_from_header(headers):
    """Extract Bearer token from Authorization header"""
    auth_header = headers.get('Authorization') or headers.get('authorization')
    
    if not auth_header:
        return None
    
    parts = auth_header.split()
    
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


def get_user_by_email(email):
    """Retrieve user from DynamoDB by email"""
    try:
        response = users_table.get_item(Key={'email': email.lower()})
        return response.get('Item')
    except Exception as e:
        print(f"Error retrieving user: {str(e)}")
        return None


def create_message(user_id, username, content, clearance_level):
    """Create a new message in DynamoDB"""
    message_id = f"msg-{uuid.uuid4()}"
    timestamp = datetime.utcnow().isoformat()
    
    message_item = {
        'messageId': message_id,
        'userId': user_id,
        'username': username,
        'content': content,
        'timestamp': timestamp,
        'clearanceLevel': clearance_level
    }
    
    try:
        messages_table.put_item(Item=message_item)
        return message_item
    except Exception as e:
        print(f"Error creating message: {str(e)}")
        raise


def lambda_handler(event, context):
    """
    Main Lambda handler to post a message
    
    Expected headers:
    Authorization: Bearer <jwt_token>
    
    Expected body:
    {
        "content": "Message content here"
    }
    """
    
    # CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    # Handle OPTIONS request for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'OK'})
        }
    
    try:
        # Extract and verify token
        request_headers = event.get('headers', {})
        token = extract_token_from_header(request_headers)
        
        if not token:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'No authorization token provided',
                    'code': 'MISSING_TOKEN'
                })
            }
        
        # Check if token is blacklisted
        if is_token_blacklisted(token):
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Token has been invalidated',
                    'code': 'TOKEN_BLACKLISTED'
                })
            }
        
        # Verify token
        is_valid, payload = verify_token(token)
        
        if not is_valid:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': payload.get('error', 'Invalid token'),
                    'code': 'INVALID_TOKEN'
                })
            }
        
        # Get user info from token
        email = payload.get('email')
        user = get_user_by_email(email)
        
        if not user:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                })
            }
        
        # Check if user is active
        if user.get('status') != 'active':
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Account is not active',
                    'code': 'ACCOUNT_NOT_ACTIVE'
                })
            }
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        content = body.get('content', '').strip()
        
        # Validate content
        if not content:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Message content is required',
                    'code': 'MISSING_CONTENT'
                })
            }
        
        if len(content) > 500:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Message content exceeds 500 characters',
                    'code': 'CONTENT_TOO_LONG'
                })
            }
        
        # Create message
        username = user.get('username', user.get('email', 'Anonymous_Cow'))
        clearance_level = user.get('clearanceLevel', 'LEVEL 1')
        
        message = create_message(
            user.get('userId'),
            username,
            content,
            clearance_level
        )
        
        # Success response
        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': message
            })
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': 'Invalid JSON in request body',
                'code': 'INVALID_JSON'
            })
        }
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
                'code': 'INTERNAL_ERROR'
            })
        }
