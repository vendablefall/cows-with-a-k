"""
AWS Lambda function for user sign-up/registration
Creates new user accounts pending council approval
"""

import json
import boto3
import hashlib
import base64
import os
import uuid
from datetime import datetime

# AWS Clients
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')
users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'CowsWithAK-Users'))

# Configuration
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@cowswithak.com')
SES_SENDER = os.environ.get('SES_SENDER', 'noreply@cowswithak.com')


def hash_password(password):
    """Hash password with salt using SHA256"""
    salt = os.urandom(32)
    
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    
    return base64.b64encode(salt).decode('utf-8'), base64.b64encode(pwd_hash).decode('utf-8')


def validate_email(email):
    """Basic email validation"""
    return '@' in email and '.' in email.split('@')[1]


def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and digit"
    
    return True, ""


def user_exists(email):
    """Check if user already exists"""
    try:
        response = users_table.get_item(
            Key={'email': email.lower()}
        )
        return 'Item' in response
    except Exception as e:
        print(f"Error checking user existence: {str(e)}")
        return False


def create_user(email, password, first_name, last_name, cow_name, profile_picture, answers):
    """Create new user in DynamoDB"""
    user_id = f"user-{uuid.uuid4()}"
    salt, pwd_hash = hash_password(password)
    
    user_item = {
        'userId': user_id,
        'email': email.lower(),
        'username': email.lower(),
        'firstName': first_name,
        'lastName': last_name,
        'cowName': cow_name,
        'passwordHash': pwd_hash,
        'passwordSalt': salt,
        'status': 'pending',
        'clearanceLevel': 'LEVEL 1',
        'answers': answers,
        'createdAt': datetime.utcnow().isoformat(),
        'lastLogin': None
    }
    
    # Add profile picture if provided
    if profile_picture:
        user_item['profilePicture'] = profile_picture.get('data', '')
        user_item['profilePictureName'] = profile_picture.get('name', '')
        user_item['profilePictureType'] = profile_picture.get('type', '')
    
    try:
        users_table.put_item(Item=user_item)
        return user_id
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        raise


def send_admin_notification(email, first_name, last_name, cow_name, answers):
    """Send email notification to admin about new registration"""
    try:
        subject = f"New Cow Registration: {cow_name} ({email})"
        
        answers_text = "\n".join([
            f"{key}: {value}"
            for key, value in answers.items()
        ])
        
        body = f"""
A new cow has requested to join the herd!

Personal Information:
- Name: {first_name} {last_name}
- Cow/Paddock Name: {cow_name}
- Email: {email}
- Registration Time: {datetime.utcnow().isoformat()}

Security Question Answers:
{answers_text}

Please review and approve/reject this registration in the admin console.

-- The Bovine Council System
"""
        
        ses.send_email(
            Source=SES_SENDER,
            Destination={'ToAddresses': [ADMIN_EMAIL]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
        
        return True
    except Exception as e:
        print(f"Error sending admin notification: {str(e)}")
        return False


def lambda_handler(event, context):
    """
    Main Lambda handler for user sign-up
    
    Expected event body:
    {
        "email": "newcow@cow.com",
        "password": "strongPassword123",
        "firstName": "John",
        "lastName": "Doe",
        "cowName": "Thunder Hooves",
        "profilePicture": "data:image/png;base64,...",
        "profilePictureName": "photo.png",
        "profilePictureType": "image/png",
        "answers": {
            "q1": "Kentucky Bluegrass",
            "q2": "Four (Correct)",
            "q3": "divine",
            "q4": "A perfect day involves..."
        }
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
        first_name = body.get('firstName', '').strip()
        last_name = body.get('lastName', '').strip()
        cow_name = body.get('cowName', '').strip()
        answers = body.get('answers', {})
        
        # Handle profile picture (base64 encoded)
        profile_picture = None
        if body.get('profilePicture'):
            profile_picture = {
                'data': body.get('profilePicture', ''),
                'name': body.get('profilePictureName', ''),
                'type': body.get('profilePictureType', '')
            }
        
        # Validate input
        if not email or not password or not first_name or not last_name or not cow_name:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Email, password, first name, last name, and cow name are required',
                    'code': 'MISSING_FIELDS'
                })
            }
        
        if not validate_email(email):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Invalid email format',
                    'code': 'INVALID_EMAIL'
                })
            }
        
        # Validate password strength
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': error_msg,
                    'code': 'WEAK_PASSWORD'
                })
            }
        
        # Check if user already exists
        if user_exists(email):
            return {
                'statusCode': 409,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'A cow with this email is already grazing in our pasture',
                    'code': 'USER_EXISTS'
                })
            }
        
        # Validate security answers
        if not answers or len(answers) < 4:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'All security questions must be answered',
                    'code': 'INCOMPLETE_ANSWERS'
                })
            }
        
        # Create user
        user_id = create_user(email, password, first_name, last_name, cow_name, profile_picture, answers)
        
        # Send notification to admin
        send_admin_notification(email, first_name, last_name, cow_name, answers)
        
        # Success response
        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': 'Registration received. The Council will review your answers.',
                'userId': user_id,
                'debugInfo': f'Email sent via AWS SES to {ADMIN_EMAIL}'
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
