#!/bin/bash
# Runs ON the EC2 instance (via SSM) - pulls secrets from Secrets Manager into
# /home/ec2-user/app/.env, then the rest of the config alongside it.
#
# Safe to re-run any time (e.g. after a secret rotation, or after terraform
# recreates the instance with a new IP) -- it always regenerates .env from
# the current public IP and the current Secrets Manager values.
set -euo pipefail

REGION="us-east-1"
PREFIX="mindedhealth"
APP_DIR="/home/ec2-user/app"
ENV_FILE="$APP_DIR/.env"

mkdir -p "$APP_DIR"

get_secret() {
  aws secretsmanager get-secret-value --region "$REGION" --secret-id "$PREFIX/$1" --query "SecretString" --output text
}

# IMDSv2: get the instance's own public IP without hardcoding it. This means
# the script never needs to be edited by hand after the EIP changes (e.g. a
# fresh `terraform apply` after the instance was torn down).
TOKEN=$(curl -sX PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
PUBLIC_IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" "http://169.254.169.254/latest/meta-data/public-ipv4")
SITE_ADDRESS="$(echo "$PUBLIC_IP" | tr '.' '-').sslip.io"

DB_PASSWORD=$(get_secret DB_PASSWORD)
DJANGO_SECRET_KEY=$(get_secret DJANGO_SECRET_KEY)
CHAT_MESSAGE_ENCRYPTION_KEY=$(get_secret CHAT_MESSAGE_ENCRYPTION_KEY)
OPENAI_API_KEY=$(get_secret OPENAI_API_KEY)
EMAIL_HOST_PASSWORD=$(get_secret EMAIL_HOST_PASSWORD)
CHAT_PROFANITY_WORDS=$(get_secret CHAT_PROFANITY_WORDS)

# Stored as one JSON secret with both halves of the RS256 key pair. Real
# newlines in the PEM text are escaped to literal "\n" here, matching
# settings.py's `.replace('\\n', '\n')` convention for a one-line .env value.
INTERNAL_JWT_KEYS_JSON=$(get_secret internal-jwt-keys)
INTERNAL_JWT_PRIVATE_KEY=$(echo "$INTERNAL_JWT_KEYS_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['INTERNAL_JWT_PRIVATE_KEY'].replace(chr(10), '\\\\n'))")
INTERNAL_JWT_PUBLIC_KEY=$(echo "$INTERNAL_JWT_KEYS_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['INTERNAL_JWT_PUBLIC_KEY'].replace(chr(10), '\\\\n'))")

cat > "$ENV_FILE" <<EOF
DJANGO_ENV=production
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
DJANGO_ALLOWED_HOSTS=${SITE_ADDRESS},${PUBLIC_IP}
SITE_ADDRESS=${SITE_ADDRESS}

OPENAI_API_KEY=${OPENAI_API_KEY}
AI_SERVICE_URL=http://ai-microservice:8001
INSIGHTS_SERVICE_URL=http://insights-service:8002

REDIS_HOST=redis
REDIS_PORT=6379

DB_NAME=mindedhealth
DB_USER=mindedhealth_user
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=postgres
DB_PORT=5432

EMAIL_HOST_USER=kettyvaisbrot@gmail.com
EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}

CHAT_MESSAGE_ENCRYPTION_KEY=${CHAT_MESSAGE_ENCRYPTION_KEY}
CHAT_PROFANITY_WORDS=${CHAT_PROFANITY_WORDS}

INTERNAL_JWT_PRIVATE_KEY=${INTERNAL_JWT_PRIVATE_KEY}
INTERNAL_JWT_PUBLIC_KEY=${INTERNAL_JWT_PUBLIC_KEY}

CELERY_BROKER_URL=redis://redis:6379/0
EOF

chmod 600 "$ENV_FILE"
chown ec2-user:ec2-user "$ENV_FILE"
echo "Wrote $ENV_FILE (site address: $SITE_ADDRESS)"
