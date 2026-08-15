import os
import sys

# Add project root directory to path
basedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, basedir)

from app import create_app
import serverless_wsgi

app = create_app('production')

def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)
