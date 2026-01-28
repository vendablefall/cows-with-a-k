"""
AWS Lambda function for user sign-out
Invalidates JWT tokens by adding them to a blacklist
"""

import json
import boto3
import os
from datetime import datetime, timedelta
import jwt

# AWS Clients
dynamodb = boto3.resource('dynamodb')
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


def blacklist_token(token, exp_timestamp):
    """Add token to blacklist table"""
    try:
        # Calculate TTL (DynamoDB will auto-delete after expiry)
        ttl = int(exp_timestamp) + (24 * 60 * 60)  # Add 24 hours buffer
        
        blacklist_table.put_item(
            Item={
                'token': token,
                'blacklistedAt': datetime.utcnow().isoformat(),
                'ttl': ttl
            }
        )
        return True
    except Exception as e:
        print(f"Error blacklisting token: {str(e)}")
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


def lambda_handler(event, context):
    """
    Main Lambda handler for user sign-out
    
    Expected headers:
    Authorization: Bearer <jwt_token>
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
        # Extract token from Authorization header
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
        
        # Blacklist the token
        exp_timestamp = payload.get('exp', datetime.utcnow().timestamp())
        blacklist_success = blacklist_token(token, exp_timestamp)
        
        if not blacklist_success:
            print("Warning: Failed to blacklist token, but proceeding with signout")
        
        # Success response
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': 'Successfully signed out. Return to the pasture safely.'
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
