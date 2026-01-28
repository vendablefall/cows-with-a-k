"""
AWS Lambda function for user sign-in
Authenticates users and returns JWT tokens
"""

import json
import boto3
import hashlib
import hmac
import base64
import os
from datetime import datetime, timedelta
import jwt

# AWS Clients
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'CowsWithAK-Users'))

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'moo-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
TOKEN_EXPIRY_HOURS = 24


def hash_password(password, salt=None):
    """Hash password with salt using SHA256"""
    if salt is None:
        salt = os.urandom(32)
    
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    
    return salt, pwd_hash


def verify_password(stored_password, stored_salt, provided_password):
    """Verify a stored password against provided password"""
    salt = base64.b64decode(stored_salt)
    _, pwd_hash = hash_password(provided_password, salt)
    stored_hash = base64.b64decode(stored_password)
    
    return hmac.compare_digest(stored_hash, pwd_hash)


def generate_jwt_token(user_data):
    """Generate JWT token for authenticated user"""
    payload = {
        'userId': user_data['userId'],
        'email': user_data['email'],
        'clearanceLevel': user_data.get('clearanceLevel', 'LEVEL 1'),
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def get_user_by_email(email):
    """Retrieve user from DynamoDB by email"""
    try:
        response = users_table.get_item(
            Key={'email': email.lower()}
        )
        return response.get('Item')
    except Exception as e:
        print(f"Error retrieving user: {str(e)}")
        return None


def update_last_login(email):
    """Update user's last login timestamp"""
    try:
        users_table.update_item(
            Key={'email': email.lower()},
            UpdateExpression='SET lastLogin = :timestamp',
            ExpressionAttributeValues={
                ':timestamp': datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        print(f"Error updating last login: {str(e)}")


def lambda_handler(event, context):
    """
    Main Lambda handler for user sign-in
    
    Expected event body:
    {
        "email": "admin@cow.com",
        "password": "moo"
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
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').strip()
        password = body.get('password', '')
        
        # Validate input
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Email and password are required',
                    'code': 'MISSING_CREDENTIALS'
                })
            }
        
        # Retrieve user from database
        user = get_user_by_email(email)
        
        if not user:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'User not authorized or account pending Council approval',
                    'code': 'INVALID_CREDENTIALS'
                })
            }
        
        # Check if user is active
        if user.get('status') != 'active':
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': f"Account is {user.get('status')}. Please contact the Council.",
                    'code': 'ACCOUNT_NOT_ACTIVE'
                })
            }
        
        # Verify password
        if not verify_password(
            user['passwordHash'],
            user['passwordSalt'],
            password
        ):
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'User not authorized or account pending Council approval',
                    'code': 'INVALID_CREDENTIALS'
                })
            }
        
        # Update last login
        update_last_login(email)
        
        # Generate JWT token
        token = generate_jwt_token(user)
        
        # Prepare user data (exclude sensitive info)
        user_data = {
            'userId': user['userId'],
            'email': user['email'],
            'username': user.get('username', user['email']),
            'clearanceLevel': user.get('clearanceLevel', 'LEVEL 1'),
            'status': user['status'],
            'createdAt': user.get('createdAt'),
            'lastLogin': datetime.utcnow().isoformat()
        }
        
        # Success response
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': 'Authentication successful',
                'token': token,
                'user': user_data
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
