# EMS CI/CD Pipeline Documentation

## **Overview**
This repository contains the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the EMS (Emergency Management System) project. The pipeline is set up using **Jenkins** to automate the processes of building, testing, and deploying the application.

This document provides an overview of the pipeline, steps to configure and run it, and troubleshooting tips for common issues.

---

## **Pipeline Overview**
The EMS CI/CD pipeline is designed to perform the following stages:

### **1. Clone Repository**
- The latest code is pulled from the repository using **Git**.

### **2. Setup Environment**
- A Python virtual environment is created, and dependencies listed in the `requirements.txt` file are installed using **pip**.

### **3. Run Tests**
- The project is tested using **pytest**.
- Test results are published in Jenkins.
- Any failing tests will cause the pipeline to stop.

### **4. Deploy Application**
- The application is deployed using **Ansible** playbooks if all tests pass and the branch is `main`.

These stages are defined in the `Jenkinsfile` located at the root of the repository.

---

## **Prerequisites**

### **1. Jenkins Installation**
- Jenkins should be installed and properly configured on your local machine, server, or cloud platform. Refer to the [Jenkins official documentation](https://www.jenkins.io/doc/) for setup instructions.

### **2. GitHub Credentials**
- Ensure that GitHub credentials are set up in Jenkins to access the repository.

### **3. Required Jenkins Plugins**
- **Git Plugin**: For repository integration.
- **Pipeline Plugin**: For scripted and declarative pipelines.
- **SSH Pipeline Steps Plugin**: For deployment tasks (if needed).

---

## **Steps to Configure the Pipeline**

### **1. Create a New Jenkins Pipeline Job**
- Navigate to the **Jenkins Dashboard** → **New Item** → **Pipeline**.
- Enter a name for the job (e.g., `EMS-CI-CD`).
- Click **OK**.

### **2. Connect to the Git Repository**
- In the pipeline configuration:
  - Under **Source Code Management**, select **Git**.
  - Enter the repository URL and credentials (if required).
  - Set the branch to `main` (or your target branch).

### **3. Define the Pipeline Script**
- Use the option **Pipeline script from SCM**.
- Specify the `Jenkinsfile` path (if it is not located in the repository's root directory).

---

## **Jenkinsfile Script**
Below is the updated `Jenkinsfile` script to automate CI/CD for the EMS project:

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from GitHub...'
                git credentialsId: 'my-repo-credentials', 
                    url: 'https://github.com/ImranJaved1073/SQE-EMS-Testing', 
                    branch: 'main'
            }
        }
        
        stage('Checkout Code') {
            steps {
                echo 'Checking out code from GitHub...'
                git branch: 'main', 
                    url: 'https://github.com/ImranJaved1073/SQE-EMS-Testing', 
                    credentialsId: 'github-token'
            }
        }
        
        stage('Install Dependencies') {
            steps {
                echo 'Installing dependencies...'
                bat 'C:\\Users\\Admin\\AppData\\Local\\Programs\\Python\\Python312\\python.exe -m pip install --upgrade pip'
                bat 'C:\\Users\\Admin\\AppData\\Local\\Programs\\Python\\Python312\\python.exe -m pip install -r requirements.txt'
            }
        }
        
        stage('Log Workspace') {
            steps {
                echo 'Logging workspace directory...'
                bat 'dir'
            }
        }
        
        stage('Build') {
            steps {
                echo 'Building the project...'
                bat '"C:\\Users\\Admin\\AppData\\Local\\Programs\\Python\\Python312\\python.exe" --version'
            }
        }

        stage('Test') {
            steps {
                echo 'Running tests...'
                bat 'set PYTHONPATH=%cd%\\src && "C:\\Users\\Admin\\AppData\\Local\\Programs\\Python\\Python312\\python.exe" -m pytest pytest_test_cases.py'
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution finished!'
        }
        success {
            echo 'Build and Test Successful!'
        }
        failure {
            echo 'An error occurred during execution.'
        }
    }
}

```

---

## **How to Run the Pipeline**

### **1. Triggering the Pipeline**
- **Automatic Trigger**: Configure GitHub webhooks to trigger the pipeline after every code commit.
- **Manual Trigger**: Navigate to the Jenkins job and click **Build Now** to run the pipeline manually.

### **2. Monitor the Pipeline**
- Check the Jenkins console output to monitor pipeline progress and troubleshoot issues.

---

## **Troubleshooting Tips**

### **1. Git Authentication Errors**
- Ensure that the GitHub credentials are correctly configured in Jenkins.
- Verify the repository URL and branch name.

### **2. Python Virtual Environment Setup Issues**
- Verify that Python 3 is installed on the Jenkins server.
- Ensure the `requirements.txt` file is present in the repository.

### **3. Test Failures**
- Review the `results.xml` file for detailed test results.
- Fix any failing tests and commit the changes to re-trigger the pipeline.

### **4. Deployment Errors**
- Ensure that Ansible is installed and configured on the Jenkins server.
- Verify the `deploy.yml` playbook for syntax and configuration issues.

---

## **Conclusion**
The EMS CI/CD pipeline ensures seamless integration and deployment of code changes. By automating key processes, it improves efficiency, reduces errors, and facilitates rapid delivery of high-quality software.
