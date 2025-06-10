# MindedHealth

MindedHealth is a comprehensive mental health tracking and management application. It helps users document various aspects of their mental health, such as sleep, exercise, food intake, meetings, and more. The app provides insights and AI-powered recommendations based on the user's data. Additionally, it features anonymous chat for communication and the option for family members to track and support their loved ones' mental health journey.

## Features

- **Mental Health Tracking**: Track daily activities such as sleep, food, exercise, mood, and more.
- **AI-powered Recommendations**: Get personalized suggestions to improve your mental health based on the tracked data.
- **Chat Functionality**: Engage in anonymous conversations with family members or support groups.
- **Data Security**: The app follows best practices to ensure user data privacy and is compliant with regulations like HIPAA.
- **Scalable & Secure**: Built using technologies like Django, Docker, Kubernetes, AWS, and PostgreSQL to provide a secure, scalable, and high-performance experience.

## Tech Stack

- **Backend**: Python, Django, Django REST Framework
- **Database**: MySQL
- **Task Queue**: Celery
- **Deployment**: Docker, Kubernetes (AWS EKS)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/kettyvaisbrot/MindedHealth.git
    ```

2. Navigate to the project directory:
    ```bash
    cd MindedHealth
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up the database and run migrations:
    ```bash
    python manage.py migrate
    ```

5. Start the development server:
    ```bash
    python manage.py runserver
    ```

6. Access the app in your browser at `http://127.0.0.1:8000/`.

## Docker Setup

1. Build the Docker image:
    ```bash
    docker build -t mindedhealth .
    ```

2. Run the Docker container:
    ```bash
    docker run -p 8000:8000 mindedhealth
    ```

## Kubernetes Setup (for AWS EKS)

1. Set up AWS EKS cluster and configure `kubectl`.

2. Deploy the app using the following commands:
    ```bash
    kubectl apply -f k8s/
    ```

## Contribution

We welcome contributions to improve MindedHealth. Feel free to fork the repository, open issues, and submit pull requests.

### How to Contribute

1. Fork the repository
2. Clone your forked repository:
    ```bash
    git clone https://github.com/kettyvaisbrot/MindedHealth.git
    ```
3. Create a feature branch:
    ```bash
    git checkout -b feature-branch
    ```
4. Make your changes, commit them:
    ```bash
    git commit -m "Description of the change"
    ```
5. Push the changes to your fork:
    ```bash
    git push origin feature-branch
    ```
6. Open a pull request on GitHub.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For any questions or inquiries, feel free to reach out:
- **Email**: kettyvaisbrot@gmail.com    
- **GitHub**: [kettyvaisbrot](https://github.com/kettyvaisbrot)
