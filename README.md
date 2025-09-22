# MindedHealth

![MindedHealth Logo](docs/logo.png)

MindedHealth is a comprehensive **mental healthcare web application** designed to help users track, document, and analyze their daily activities, habits, and mental health trends. The platform also provides AI-driven insights and recommendations based on users’ data, enabling more proactive mental health management.

---

## **Features**

- **Dashboard & Activity Tracking**
  - Log daily activities: sleep, exercise, meals, meetings, and seizures.
  - Keep detailed documentation for each category.

- **AI Microservice Insights**
  - Analyze recorded data and provide actionable insights.
  - Fully automated suggestions and personalized recommendations.

- **Family Access**
  - Family members can view and contribute to certain activity logs.
  - Separate family chat for collaboration and support.

- **Anonymous Chat**
  - Users can communicate anonymously with peers in a safe environment.

- **Authentication & Security**
  - OAuth2 / JWT authentication.
  - Secure storage and encryption of user data (HIPAA-ready).

- **Modern Tech Stack**
  - Django REST Framework, PostgreSQL, Redis, Celery
  - Docker & Kubernetes deployment
  - CI/CD automation with GitHub Actions
  - Event-driven architecture with monitoring via Prometheus and Grafana

---

## **Visit MindedHealth**

Currently, MindedHealth can be deployed locally or on **AWS EKS** using Docker and Kubernetes.

- **Local Development:** See instructions below.
- **Cloud Deployment:** Access the app via your AWS EKS LoadBalancer URL or your custom domain after deployment.

---

## **Local Development Setup**

### **Prerequisites**

- Python 3.11+
- Docker & Docker Compose
- Node.js (if using frontend build tools)
- PostgreSQL (or Dockerized Postgres)
- Git

---

### **Clone the Repository**
git clone https://github.com/kettyvaisbrot/MindedHealth.git
cd MindedHealth