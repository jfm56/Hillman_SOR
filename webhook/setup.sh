#!/bin/bash
set -e

echo "Setting up auto-deploy webhook..."

# Generate webhook secret
WEBHOOK_SECRET=$(openssl rand -hex 20)
echo "Generated webhook secret: $WEBHOOK_SECRET"
echo ""
echo "SAVE THIS SECRET - you'll need it for GitHub!"
echo ""

# Update service file with secret
sed -i "s/your-webhook-secret-here/$WEBHOOK_SECRET/" /root/hillmann-ai/webhook/webhook.service

# Install systemd service
sudo cp /root/hillmann-ai/webhook/webhook.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable webhook
sudo systemctl start webhook

# Open firewall port
sudo ufw allow 9000/tcp

echo ""
echo "=========================================="
echo "  Webhook Setup Complete!"
echo "=========================================="
echo ""
echo "Webhook URL: http://$(curl -s ifconfig.me):9000/webhook"
echo "Secret: $WEBHOOK_SECRET"
echo ""
echo "Now add this webhook to GitHub:"
echo "1. Go to: https://github.com/jfm56/Hillman_SOR/settings/hooks"
echo "2. Click 'Add webhook'"
echo "3. Payload URL: http://YOUR_SERVER_IP:9000/webhook"
echo "4. Content type: application/json"
echo "5. Secret: $WEBHOOK_SECRET"
echo "6. Events: Just the push event"
echo "7. Click 'Add webhook'"
echo ""
echo "Test with: curl http://localhost:9000/health"
