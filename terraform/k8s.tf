resource "kubernetes_namespace" "mindedhealth" {
  metadata { name = "mindedhealth" }
}

# Django Deployment + Service
resource "kubernetes_deployment" "django" {
  metadata {
    name      = "mindedhealth-django"
    namespace = kubernetes_namespace.mindedhealth.metadata[0].name
    labels = { app = "mindedhealth-django" }
  }
  spec {
    replicas = 2
    selector { match_labels = { app = "mindedhealth-django" } }
    template {
      metadata { labels = { app = "mindedhealth-django" } }
      spec {
        container {
          name  = "django"
          image = "${aws_ecr_repository.django.repository_url}:latest"
          port { container_port = 8000 }
          env {
            name  = "DJANGO_SETTINGS_MODULE"
            value = "MindedHealth.settings"
          }
          # add envFrom secretRef or env secrets for DB / SECRET_KEY in prod
        }
      }
    }
  }
}

resource "kubernetes_service" "django" {
  metadata {
    name      = "mindedhealth-django"
    namespace = kubernetes_namespace.mindedhealth.metadata[0].name
  }
  spec {
    selector = { app = "mindedhealth-django" }
    port {
      port        = 8000
      target_port = 8000
    }
    type = "ClusterIP"
  }
}

# AI microservice Deployment + Service
resource "kubernetes_deployment" "ai" {
  metadata {
    name      = "mindedhealth-ai"
    namespace = kubernetes_namespace.mindedhealth.metadata[0].name
    labels = { app = "mindedhealth-ai" }
  }
  spec {
    replicas = 1
    selector { match_labels = { app = "mindedhealth-ai" } }
    template {
      metadata { labels = { app = "mindedhealth-ai" } }
      spec {
        container {
          name  = "ai"
          image = "${aws_ecr_repository.ai.repository_url}:latest"
          port { container_port = 8001 }
          env {
            name = "OPENAI_API_KEY"
            value_from {
              secret_key_ref {
                name = "openai-secret"
                key  = "OPENAI_API_KEY"
              }
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "ai" {
  metadata {
    name      = "mindedhealth-ai"
    namespace = kubernetes_namespace.mindedhealth.metadata[0].name
  }
  spec {
    selector = { app = "mindedhealth-ai" }
    port {
      port        = 8001
      target_port = 8001
    }
    type = "ClusterIP"
  }
}
