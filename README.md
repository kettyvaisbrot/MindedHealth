# MindedHealth

MindedHealth is a **mental healthcare backend system** designed to help users document daily activities, track mental health-related data, and receive AI-assisted insights based on historical patterns.

The project focuses on **backend architecture, scalability, and reliability**, and demonstrates how a Django-based system evolves into a microservices-oriented architecture.

---

## Project Purpose

The goal of MindedHealth is to:

- Enable structured tracking of mental health–related activities (sleep, exercise, meals, meetings, seizures)
- Generate AI-driven insights based on recent and historical data
- Support collaboration between users and family members
- Demonstrate production-oriented backend practices such as security, fault tolerance, and observability

This system is actively deployed on AWS and is used by real users and licensed therapists in a production environment.

The repository is shared for technical review and collaboration purposes, with a focus on backend architecture, scalability, reliability, and system design decisions made while operating a real healthcare-oriented platform.

---

## High-Level Architecture

MindedHealth follows a **hybrid architecture**, combining a Django modular monolith with independently deployable microservices.

The system is currently in an **active migration phase**, gradually extracting domain-specific services while maintaining production stability.

---

### Core Backend (Django – Modular Core)

The primary backend is implemented as a **modular Django service**, responsible for:

- Core domain models and business logic
- User management and authentication
- Activity tracking and persistence
- Family access and role-based permissions
- Orchestration of background jobs via Celery

Although deployed as a single service, the codebase is structured to support gradual extraction of domain-specific services as usage and scaling requirements grow.

---

### Insights Service (FastAPI – Microservice)

The insights service is responsible for **processing and preparing data for AI generation**.

Responsibilities include:

- Processing aggregated user activity data
- Computing metrics and correlations
- Building structured prompts for AI generation
- Managing caching (Redis)

---

### AI Microservice (FastAPI – Microservice)

The AI microservice is responsible for **handling all communication with the AI model**.

Responsibilities include:

- Receiving prompts from the insights service
- Communicating with the AI model
- Handling retries, timeouts, and failure scenarios
- Returning generated insights

This separation allows **independent scaling, fault isolation, and cleaner system boundaries**.

---

## AI Insights Generation Flow

The AI insights feature is implemented as a multi-step pipeline across services:

User
↓
Django Monolith (fetch logs, serialize data)
↓
POST → insights_service
↓
process data + build prompt + caching
↓
POST → ai_microservice
↓
OpenAI API (LLM)
↓
ai_microservice returns insight
↓
insights_service caches + returns
↓
Django → User


**Flow:** Django → insights_service → ai_microservice → OpenAI → back to user

---

## Infrastructure Components

- **PostgreSQL** – primary relational data store  
- **Redis** – caching, session support, and asynchronous task coordination  
- **Docker** – containerization for consistent environments  
- **Kubernetes (EKS)** – orchestration and service scaling  
- **Terraform** – infrastructure provisioning and environment reproducibility  

Inter-service communication currently uses synchronous HTTP calls, with fault-tolerance mechanisms such as timeouts, retries, and caching applied where appropriate. Additional asynchronous and event-driven patterns are planned as part of the ongoing migration.

---

## Features

### Activity Tracking

- Daily documentation of:
  - Sleep
  - Exercise
  - Meals
  - Meetings
  - Seizures
- Each category is modeled separately for clarity and analytics.

---

### AI-Driven Insights

- Multi-service pipeline (Insights Service + AI Microservice)
- Automated insight generation based on recent activity history
- Cached results to minimize repeated AI calls

---

### Family Access

- Family members can view and contribute to selected activity logs
- Role-based access control

---

### Anonymous Chat

- Anonymous peer communication
- Designed to avoid storing sensitive personal identifiers

---

### Authentication & Security

- OAuth2 / JWT-based authentication
- Secrets managed via environment variables
- Architecture designed with healthcare privacy considerations in mind (HIPAA-aware, not certified)

---

## Tech Stack

### Backend

- Python 3.11
- Django & Django REST Framework
- FastAPI (microservices)

### Data & Async

- PostgreSQL
- Redis
- Celery

### Infrastructure

- Docker & Docker Compose
- Kubernetes (AWS EKS)
- Terraform
- GitHub Actions (CI/CD)

---

## Running the Project Locally

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

### Clone the Repository

git clone https://github.com/kettyvaisbrot/MindedHealth.git
cd MindedHealth
