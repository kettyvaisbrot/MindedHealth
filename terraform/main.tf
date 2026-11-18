#######################
# VPC (network layer) #
#######################

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-vpc"
  cidr = "10.0.0.0/16"

  azs = [
    "${var.aws_region}a",
    "${var.aws_region}b"
  ]

  public_subnets = [
    "10.0.1.0/24",
    "10.0.2.0/24"
  ]

  private_subnets = [
    "10.0.11.0/24",
    "10.0.12.0/24"
  ]

  # No NAT Gateway: the private subnets only hold RDS, which needs no
  # outbound internet access. The app server lives in a public subnet instead.
  enable_nat_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  map_public_ip_on_launch = true
}

#####################################
# EC2 (single app server, all svcs) #
#####################################

resource "aws_security_group" "app_sg" {
  name        = "${var.project_name}-app-sg"
  description = "App server: HTTP/HTTPS in, no SSH port (access via SSM)"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "HTTP (redirects to HTTPS via Caddy)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project_name}-app-sg"
    Project = var.project_name
  }
}

# Lets SSM connect to the instance without opening an SSH port or managing keys.
resource "aws_iam_role" "app_ssm_role" {
  name = "${var.project_name}-app-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })

  tags = {
    Project = var.project_name
  }
}

resource "aws_iam_role_policy_attachment" "app_ssm_policy" {
  role       = aws_iam_role.app_ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Lets the instance read its own secrets (DB password, API keys, etc.) from
# Secrets Manager at deploy time instead of them ever touching source control.
resource "aws_iam_role_policy" "app_secrets_manager_access" {
  name = "${var.project_name}-app-secrets-manager-access"
  role = aws_iam_role.app_ssm_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "ReadOwnSecrets"
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = "arn:aws:secretsmanager:${var.aws_region}:*:secret:${var.project_name}/*"
    }]
  })
}

resource "aws_iam_instance_profile" "app_ssm_profile" {
  name = "${var.project_name}-app-ssm-profile"
  role = aws_iam_role.app_ssm_role.name
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  # "al2023-ami-*-x86_64" also matches the "minimal" variant
  # (al2023-ami-minimal-...), which ships WITHOUT the SSM agent
  # pre-installed -- the instance would never register with SSM. The
  # standard image's name starts with a version number right after
  # "al2023-ami-", so this pattern excludes "minimal-" specifically.
  filter {
    name   = "name"
    values = ["al2023-ami-2*-x86_64"]
  }
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.app_instance_type
  subnet_id              = module.vpc.public_subnets[0]
  vpc_security_group_ids = [aws_security_group.app_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.app_ssm_profile.name

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  user_data = <<-EOF
    #!/bin/bash
    # 1GB RAM runs Django + 2 FastAPI services + Postgres + Redis + Caddy
    # at once -- a swap file keeps the kernel from OOM-killing one of them
    # under a momentary memory spike instead of just running slower.
    fallocate -l 1G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab

    dnf install -y docker
    systemctl enable --now docker
    curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    usermod -aG docker ec2-user
  EOF

  tags = {
    Name    = "${var.project_name}-app"
    Project = var.project_name
  }
}

resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"

  tags = {
    Name    = "${var.project_name}-app-eip"
    Project = var.project_name
  }
}


#############################################
# GitHub Actions OIDC (no long-lived keys)  #
#############################################

resource "aws_iam_openid_connect_provider" "github_actions" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

# Trust policy: only workflows running on main, in this exact repo, may
# assume this role -- no other repo or branch can, even with the role ARN.
resource "aws_iam_role" "github_actions_deploy" {
  name = "${var.project_name}-github-actions-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github_actions.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:kettyvaisbrot/MindedHealth:ref:refs/heads/main"
        }
      }
    }]
  })

  tags = {
    Project = var.project_name
  }
}

# Just enough to trigger a deploy command on the one app server -- nothing else.
resource "aws_iam_role_policy" "github_actions_deploy_policy" {
  name = "${var.project_name}-github-actions-deploy-policy"
  role = aws_iam_role.github_actions_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SendDeployCommand"
        Effect = "Allow"
        Action = "ssm:SendCommand"
        Resource = [
          aws_instance.app.arn,
          "arn:aws:ssm:${var.aws_region}::document/AWS-RunShellScript"
        ]
      },
      {
        # SSM's GetCommandInvocation does not support resource-level
        # restriction, so this is scoped by action only.
        Sid      = "ReadDeployCommandResult"
        Effect   = "Allow"
        Action   = "ssm:GetCommandInvocation"
        Resource = "*"
      },
      {
        # Lets the deploy workflow look up the current instance ID by its
        # Name tag instead of a hardcoded ID, so it keeps working after
        # terraform recreates the instance. DescribeInstances has no
        # resource-level restriction in IAM, hence "*" -- it is read-only.
        Sid      = "LookUpAppInstance"
        Effect   = "Allow"
        Action   = "ec2:DescribeInstances"
        Resource = "*"
      }
    ]
  })
}
