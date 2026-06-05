# 🚀 Two-Tier Flask App — End-to-End CI/CD Deployment on AWS

A production-style, two-tier web application featuring a Python Flask backend and a MySQL database. This project demonstrates full infrastructure provisioning, containerization, and an automated CI/CD pipeline deployed on cloud infrastructure.

*The base application logic is adapted from [`prashantgohel321/DevOps-Project-Two-Tier-Flask-App`](https://github.com/prashantgohel321/DevOps-Project-Two-Tier-Flask-App). My work focused on provisioning the cloud infrastructure, resolving build and runtime constraints, and building the automated deployment pipeline.*

---

## 🛠️ Tech Stack & Ecosystem

| Layer | Technologies Used |
| :--- | :--- |
| **Cloud & Infrastructure** | AWS EC2 (Ubuntu), Security Groups |
| **Containerization & Orchestration** | Docker, Docker Compose |
| **CI/CD Automation** | Jenkins (Pipeline-as-Code), GitHub |
| **Backend Application** | Python 3, Flask, PyMySQL, Cryptography |
| **Database Tier** | MySQL 8 |

---

## 📐 Architecture & Workflow

```text
[ GitHub Push ]
       │
       ▼ (Poll SCM / Webhook)
┌────────────── AWS EC2 Instance ─────────────────────────┐
│                                                         │
│   ┌──────────────┐      Builds & Deploys                │
│   │   Jenkins    │───────────────────────────────┐      │
│   │ (Port 8080)  │                                │      │
│   └──────────────┘                                ▼      │
│                                        ┌────────────────┐│
│                                        │ Docker Compose ││
│                                        └────────┬───────┘│
│                                                 │        │
│                       ┌─────────────────────────┴────┐   │
│                       ▼                              ▼   │
│              ┌─────────────────┐            ┌───────────┐│
│              │ Flask App Layer │──(Waits)──>│  MySQL DB ││
│              │   (Port 5000)   │            │(Port 3306)││
│              └─────────────────┘            └───────────┘│
└───────────────────────│──────────────────────────────────┘
                        ▼
                [ Public Access ]
```

1. **Push:** Code is committed and pushed to GitHub.
2. **Trigger:** Jenkins detects the new commit (via Poll SCM or a GitHub webhook).
3. **Pipeline Execution:** Jenkins clones the repo, runs the declarative `Jenkinsfile`, and invokes Docker Compose.
4. **Orchestrated Rollout:** Docker Compose tears down old containers, rebuilds the updated Flask image, and brings the network services back up.

---

## ⚡ Key Engineering Challenges & Solutions

Deploying a template repository onto real, resource-constrained cloud infrastructure exposed several hidden bottlenecks. Here is how I re-engineered the setup to make it reliable:

### 1. Lightweight Build Optimization (Driver Migration)

* **The Problem:** The original project relied on `mysqlclient`, which compiles C extensions via `gcc`. On a memory-constrained **AWS t2.micro instance (1 GB RAM)**, this compilation step ran out of memory and repeatedly failed the build.
* **The Solution:** I migrated the database driver to **`PyMySQL`** (pure Python) with the `cryptography` library. This eliminated the heavy binary compilation entirely, taking the build from several minutes (and failing) to a few seconds of stable execution.

### 2. Eliminating Database Race Conditions (Resilient Startup)

* **The Problem:** Docker Compose starts containers together. MySQL takes several seconds to initialize before it accepts connections, so the Flask container connected too early, failed, and crash-looped.
* **The Solution:** I added a **retry loop** to the Flask database-initialization logic. The app now polls and waits for MySQL to become available before serving requests, making cold starts reliable.

### 3. MySQL 8 Authentication Compatibility

* **The Problem:** MySQL 8 uses `caching_sha2_password` as its default authentication method, which PyMySQL cannot complete without an extra dependency.
* **The Solution:** Added the Python `cryptography` package to the runtime so the secure SHA-2 handshake works without weakening the database's default auth.

### 4. Hardening Jenkins on a Constrained Node

* **The Problem:** Jenkins took its built-in node offline due to a low-disk-space check against the tiny RAM-backed `/tmp`, which blocked all builds from scheduling.
* **The Solution:** Remapped Jenkins' temporary directory to the main disk and adjusted the disk-space monitor thresholds so the controller node stayed online and builds could run.

---

## 📂 Project Structure

```bash
├── diagrams/              # Architecture and workflow diagrams
├── templates/             # Flask HTML frontend views
├── app.py                 # Core Flask application + resilient DB retry logic
├── Dockerfile             # Application image build recipe
├── docker-compose.yml     # Multi-container network and volume orchestration
├── Jenkinsfile            # Declarative pipeline-as-code automation script
├── message.sql            # Optional database seed file
├── requirements.txt       # Python dependency manifest (no compiled drivers)
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

* An AWS account with a running Ubuntu EC2 instance.
* Inbound Security Group rules for ports: `22` (SSH), `5000` (Flask app), and `8080` (Jenkins).

### Manual Deployment

To run the multi-container setup manually on your server:

1. Clone the repository:

```bash
   git clone https://github.com/Amirtha655/two-tier-flask-cicd.git
   cd two-tier-flask-cicd
```

2. Spin up the environment with Docker Compose:

```bash
   docker compose up -d --build
```

3. Access the web application at `http://<your-ec2-public-ip>:5000`

### Automated CI/CD Setup

1. Install **Docker** and **Jenkins** on your EC2 instance.
2. Add the `jenkins` user to the `docker` group:

```bash
   sudo usermod -aG docker jenkins && sudo systemctl restart jenkins
```

3. Create a **Pipeline** project in Jenkins pointing to this GitHub repository (Pipeline script from SCM → `Jenkinsfile`, branch `main`).
4. Enable automatic deploys with **one** of:
   * **Poll SCM:** in the job config, set the schedule to `* * * * *`, or
   * **GitHub Webhook:** add a webhook for `push` events pointing to `http://<your-ec2-ip>:8080/github-webhook/`.
5. Push a commit and watch Jenkins build and deploy automatically.
