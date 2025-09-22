output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "kubeconfig" {
  value = module.eks.kubeconfig
}

output "vpc_id" {
  value = module.vpc.vpc_id
}
