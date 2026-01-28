"""
AWS Lambda function to retrieve message board messages
Gets paginated messages from DynamoDB
"""

import json
import boto3
import os
from datetime import datetime
import jwt
from decimal import Decimal

# AWS Clients
dynamodb = boto3.resource('dynamodb')
messages_table = dynamodb.Table(os.environ.get('MESSAGES_TABLE', 'CowsWithAK-Messages'))
blacklist_table = dynamodb.Table(os.environ.get('BLACKLIST_TABLE', 'CowsWithAK-TokenBlacklist'))

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'moo-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


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


def get_messages(limit=50, last_key=None):
    """Retrieve messages from DynamoDB with pagination"""
    try:
        scan_kwargs = {
            'Limit': min(limit, 100),
            'IndexName': 'timestamp-index'  # Assumes GSI on timestamp for chronological order
        }
        
        if last_key:
            scan_kwargs['ExclusiveStartKey'] = {'messageId': last_key}
        
        # Scan in reverse chronological order
        response = messages_table.scan(**scan_kwargs)
        
        items = response.get('Items', [])
        
        # Sort by timestamp descending (newest first)
        items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Convert Decimal to float for JSON serialization
        messages = []
        for item in items:
            message = {
                'messageId': item.get('messageId'),
                'userId': item.get('userId'),
                'username': item.get('username'),
                'content': item.get('content'),
                'timestamp': item.get('timestamp'),
                'clearanceLevel': item.get('clearanceLevel', 'LEVEL 1')
            }
            messages.append(message)
        
        result = {
            'messages': messages
        }
        
        # Add pagination key if there are more results
        if 'LastEvaluatedKey' in response:
            result['lastKey'] = response['LastEvaluatedKey'].get('messageId')
        
        return result
        
    except Exception as e:
        print(f"Error retrieving messages: {str(e)}")
        raise


def lambda_handler(event, context):
    """
    Main Lambda handler to get message board messages
    
    Expected headers:
    Authorization: Bearer <jwt_token>
    
    Query parameters:
    - limit: Maximum number of messages (default 50, max 100)
    - lastKey: Last message ID for pagination
    """
    
    # CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
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
        
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        limit = int(query_params.get('limit', 50))
        last_key = query_params.get('lastKey')
        
        # Retrieve messages
        result = get_messages(limit, last_key)
        
        # Success response
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                **result
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
