output "app_public_ip" {
  description = "Elastic IP of the app server"
  value       = aws_eip.app.public_ip
}

output "app_instance_id" {
  description = "Instance ID – used with 'aws ssm start-session --target <id>' to connect"
  value       = aws_instance.app.id
}

output "rds_endpoint" {
  description = "PostgreSQL endpoint"
  value       = aws_db_instance.postgres.address
}

output "rds_db_name" {
  description = "DB name"
  value       = aws_db_instance.postgres.db_name
}

output "github_actions_role_arn" {
  description = "Paste this into the deploy.yml workflow's role-to-assume"
  value       = aws_iam_role.github_actions_deploy.arn
}
