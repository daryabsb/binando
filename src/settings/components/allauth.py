ACCOUNT_LOGIN_REDIRECT_URL = '/'  # Default redirect after login (if 'next' is not provided)
LOGIN_REDIRECT_URL = '/'  # Fallback redirect after login

# Define session timeout in seconds (e.g., 3600 seconds = 1 hour)
SESSION_COOKIE_AGE = 3600

# Expire the session when the user closes the browser
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Optional: Use persistent sessions (default is True)
# SESSION_SAVE_EVERY_REQUEST = True