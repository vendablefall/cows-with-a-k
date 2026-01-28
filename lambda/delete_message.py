"""
AWS Lambda function to delete messages from the message board
Allows users to delete their own messages or admins to delete any message
"""

import json
import boto3
import os
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


def get_message(message_id):
    """Retrieve message from DynamoDB"""
    try:
        response = messages_table.get_item(Key={'messageId': message_id})
        return response.get('Item')
    except Exception as e:
        print(f"Error retrieving message: {str(e)}")
        return None


def delete_message(message_id):
    """Delete message from DynamoDB"""
    try:
        messages_table.delete_item(Key={'messageId': message_id})
        return True
    except Exception as e:
        print(f"Error deleting message: {str(e)}")
        return False


def lambda_handler(event, context):
    """
    Main Lambda handler to delete a message
    
    Expected headers:
    Authorization: Bearer <jwt_token>
    
    Path parameters:
    - messageId: ID of the message to delete
    """
    
    # CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'DELETE,OPTIONS'
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
        
        # Get message ID from path parameters
        path_params = event.get('pathParameters') or {}
        message_id = path_params.get('messageId')
        
        if not message_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Message ID is required',
                    'code': 'MISSING_MESSAGE_ID'
                })
            }
        
        # Retrieve the message
        message = get_message(message_id)
        
        if not message:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Message not found',
                    'code': 'MESSAGE_NOT_FOUND'
                })
            }
        
        # Check authorization: user must own the message or be TOP SECRET clearance
        user_id = user.get('userId')
        is_admin = user.get('clearanceLevel') == 'TOP SECRET'
        is_owner = message.get('userId') == user_id
        
        if not (is_owner or is_admin):
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Not authorized to delete this message',
                    'code': 'FORBIDDEN'
                })
            }
        
        # Delete the message
        success = delete_message(message_id)
        
        if not success:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Failed to delete message',
                    'code': 'DELETE_FAILED'
                })
            }
        
        # Success response
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': 'Message deleted successfully'
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
