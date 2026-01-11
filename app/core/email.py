# core/email.py
"""
Email utilities using Resend
Handles sending password reset emails
"""

import resend
import os
import random
from fastapi import HTTPException, status

# ============================================================================
# CONFIGURATION
# ============================================================================

# Get Resend API key from environment variable
# IMPORTANT: Set this in your .env file or environment
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
resend.api_key = RESEND_API_KEY

# Email configuration
FROM_EMAIL = os.getenv("FROM_EMAIL", "Exodus_support@resend.dev")  # Update with your verified domain
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")  # Update with your frontend URL

# ============================================================================
# OTP GENERATION
# ============================================================================

def generate_otp() -> str:
    """
    Generate a random 6-digit OTP
    
    Returns:
        6-digit OTP as string (e.g., "123456")
    """
    return str(random.randint(100000, 999999))

# ============================================================================
# EMAIL SENDING FUNCTIONS
# ============================================================================

def send_password_reset_email(email: str, otp: str) -> bool:
    """
    Send password reset email with OTP link
    
    Args:
        email: Recipient email address
        otp: 6-digit OTP code
    
    Returns:
        True if email sent successfully, False otherwise
    
    Raises:
        HTTPException if email sending fails
    """
    
    # Build the reset link with OTP as query parameter
    reset_link = f"{FRONTEND_URL}/reset-password?otp={otp}"
    
    # Email HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: black;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 5px 5px 0 0;
            }}
            .content {{
                background-color: #f9fafb;
                padding: 30px;
                border-radius: 0 0 5px 5px;
            }}
            .otp {{
                font-size: 32px;
                font-weight: bold;
                color: black;
                letter-spacing: 5px;
                text-align: center;
                padding: 20px;
                background-color: white;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background-color: black;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 20px;
                color: #6b7280;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset Request</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>We received a request to reset your password. Use the code below to reset your password:</p>
                
                <div class="otp">{otp}</div>
                
                <p>Or click the button below to reset your password:</p>
                
                <a href="{reset_link}" class="button">Reset Password</a>
                
                <p><strong>This code will expire in 30 minutes.</strong></p>
                
                <p>If you didn't request a password reset, please ignore this email or contact support if you have concerns.</p>
                
                <p>Best regards,<br>Your Team</p>
            </div>
            <div class="footer">
                <p>This is an automated email. Please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version (fallback)
    text_content = f"""
    Password Reset Request
    
    Hello,
    
    We received a request to reset your password. Use the code below to reset your password:
    
    {otp}
    
    Or visit this link: {reset_link}
    
    This code will expire in 30 minutes.
    
    If you didn't request a password reset, please ignore this email.
    
    Best regards,
    Your Team
    """
    
    try:
        # Send email using Resend
        params = {
            "from": FROM_EMAIL,
            "to": [email],
            "subject": "Password Reset Request",
            "html": html_content,
            "text": text_content
        }
        
        response = resend.Emails.send(params)
        
        return True
        
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send password reset email: {str(e)}"
        )


# ============================================================================
# ============================================================================
# ============================================================================
