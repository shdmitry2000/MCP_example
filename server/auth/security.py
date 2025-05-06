import os
import time
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import hashlib
import secrets
import base64

class SecurityManager:
    """Manages security features for MCP server."""
    
    def __init__(self, secret_key: Optional[str] = None, token_expiry: int = 60 * 60):
        """
        Initialize security manager.
        
        Args:
            secret_key: Secret key for JWT signing (generated if None)
            token_expiry: Token expiry time in seconds (default: 1 hour)
        """
        self.secret_key = secret_key or os.environ.get("MCP_SECRET_KEY") or self._generate_secret_key()
        self.token_expiry = token_expiry
        self.allowed_users = {}  # username -> hashed_password
        self.active_tokens = {}  # token -> expiry_time
    
    def _generate_secret_key(self) -> str:
        """Generate a secure random secret key."""
        return secrets.token_hex(32)
    
    def hash_password(self, password: str) -> str:
        """Hash a password securely."""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return base64.b64encode(salt + key).decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        try:
            # Decode the stored hash
            decoded = base64.b64decode(hashed_password.encode('utf-8'))
            salt, stored_key = decoded[:32], decoded[32:]
            
            # Hash the provided password with the same salt
            key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                100000
            )
            
            # Compare the keys
            return key == stored_key
        except Exception:
            return False
    
    def add_user(self, username: str, password: str) -> None:
        """Add a user with a hashed password."""
        self.allowed_users[username] = self.hash_password(password)
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate a user by username and password."""
        if username not in self.allowed_users:
            return False
        
        return self.verify_password(password, self.allowed_users[username])
    
    def generate_token(self, username: str, scopes: Optional[List[str]] = None) -> str:
        """
        Generate a JWT token for an authenticated user.
        
        Args:
            username: Username
            scopes: Optional list of permission scopes
            
        Returns:
            JWT token
        """
        # Create token payload
        payload = {
            "sub": username,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=self.token_expiry)
        }
        
        if scopes:
            payload["scopes"] = scopes
        
        # Generate token
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        # Store token
        self.active_tokens[token] = time.time() + self.token_expiry
        
        return token
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            Token payload if valid, None otherwise
        """
        # Check if token exists and is not expired
        if token not in self.active_tokens or self.active_tokens[token] < time.time():
            # Remove expired token
            if token in self.active_tokens:
                del self.active_tokens[token]
            return None
        
        try:
            # Decode and validate token
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.PyJWTError:
            # Invalid token
            if token in self.active_tokens:
                del self.active_tokens[token]
            return None
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            True if token was revoked, False otherwise
        """
        if token in self.active_tokens:
            del self.active_tokens[token]
            return True
        return False
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens.
        
        Returns:
            Number of removed tokens
        """
        current_time = time.time()
        expired_tokens = [token for token, expiry in self.active_tokens.items() if expiry < current_time]
        
        for token in expired_tokens:
            del self.active_tokens[token]
        
        return len(expired_tokens)