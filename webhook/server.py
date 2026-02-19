#!/usr/bin/env python3
"""
Simple webhook server for auto-deployment on git push.
Listens for GitHub webhook POST requests and triggers deployment.
"""
import os
import hmac
import hashlib
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your-webhook-secret')
DEPLOY_PATH = os.environ.get('DEPLOY_PATH', '/root/hillmann-ai')
PORT = int(os.environ.get('WEBHOOK_PORT', 9000))


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature:
        return False
    expected = 'sha256=' + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def deploy():
    """Run deployment commands."""
    print("Starting deployment...")
    os.chdir(DEPLOY_PATH)
    
    commands = [
        ['git', 'fetch', 'origin'],
        ['git', 'reset', '--hard', 'origin/main'],
        ['docker', 'compose', '-f', 'docker-compose.prod.yml', 'up', '-d', '--build'],
    ]
    
    for cmd in commands:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        print(result.stdout)
    
    print("Deployment complete!")
    return True


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/webhook':
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get('Content-Length', 0))
        payload = self.rfile.read(content_length)
        signature = self.headers.get('X-Hub-Signature-256', '')

        # Verify signature
        if not verify_signature(payload, signature):
            print("Invalid signature")
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'Invalid signature')
            return

        # Parse payload
        try:
            data = json.loads(payload)
            ref = data.get('ref', '')
            
            # Only deploy on push to main branch
            if ref == 'refs/heads/main':
                print(f"Received push to main branch")
                success = deploy()
                
                self.send_response(200 if success else 500)
                self.end_headers()
                self.wfile.write(b'Deployed' if success else b'Deploy failed')
            else:
                print(f"Ignoring push to {ref}")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Ignored')
                
        except Exception as e:
            print(f"Error: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == '__main__':
    print(f"Webhook server starting on port {PORT}")
    print(f"Deploy path: {DEPLOY_PATH}")
    server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
    server.serve_forever()
