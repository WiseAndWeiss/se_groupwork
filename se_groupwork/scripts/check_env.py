#!/usr/bin/env python3
import os
import sys

required_env_vars = [
    'MYSQL_ROOT_PASSWORD',
    'MYSQL_DATABASE', 
    'MYSQL_USER',
    'MYSQL_PASSWORD',
    'SECRET_KEY',
    'SCHEDULER_TZ'
]

def check_environment():
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    else:
        print("All required environment variables are set")
        sys.exit(0)

if __name__ == '__main__':
    check_environment()