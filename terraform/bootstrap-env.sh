#!/bin/bash
# Runs ON the EC2 instance (via SSM) - pulls secrets from Secrets Manager into
# /home/ec2-user/app/.env, then the rest of the config alongside it.
set -euo pipefail

REGION="us-east-1"
PREFIX="mindedhealth"
APP_DIR="/home/ec2-user/app"
ENV_FILE="$APP_DIR/.env"

mkdir -p "$APP_DIR"

get_secret() {
  aws secretsmanager get-secret-value --region "$REGION" --secret-id "$PREFIX/$1" --query "SecretString" --output text
}

DB_PASSWORD=$(get_secret DB_PASSWORD)
DJANGO_SECRET_KEY=$(get_secret DJANGO_SECRET_KEY)
CHAT_MESSAGE_ENCRYPTION_KEY=$(get_secret CHAT_MESSAGE_ENCRYPTION_KEY)
OPENAI_API_KEY=$(get_secret OPENAI_API_KEY)
EMAIL_HOST_PASSWORD=$(get_secret EMAIL_HOST_PASSWORD)

cat > "$ENV_FILE" <<EOF
DJANGO_ENV=production
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
DJANGO_ALLOWED_HOSTS=3-214-210-234.sslip.io,3.214.210.234

OPENAI_API_KEY=${OPENAI_API_KEY}
AI_SERVICE_URL=http://ai-microservice:8001
INSIGHTS_SERVICE_URL=http://insights-service:8002

REDIS_HOST=redis
REDIS_PORT=6379

DB_NAME=mindedhealth
DB_USER=mindedhealth_user
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=mindedhealth-postgres.c30a6w0247um.us-east-1.rds.amazonaws.com
DB_PORT=5432

EMAIL_HOST_USER=kettyvaisbrot@gmail.com
EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}

CHAT_MESSAGE_ENCRYPTION_KEY=${CHAT_MESSAGE_ENCRYPTION_KEY}

CELERY_BROKER_URL=redis://redis:6379/0
EOF

chmod 600 "$ENV_FILE"
chown ec2-user:ec2-user "$ENV_FILE"
echo "Wrote $ENV_FILE"
