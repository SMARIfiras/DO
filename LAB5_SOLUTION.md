# Lab 5: API Integration Testing, Frontend Containerization, Docker Compose & CI/CD Pipelines
## Solution Complète & Rapport Technique (Pair Assignment)

**Université :** Université Abdelhamid Mehri - Constantine 2 • Faculté des NTIC  
**Spécialité :** Ingénieurs en Cybersécurité (5ème Année)  
**Module :** DevOps  
**Architecture :** Event Manager API (FastAPI, SQLAlchemy, SQLite, Frontend HTML5/JS, Docker Compose, GitHub Actions)  

---

## 1. Vue d'ensemble de l'Architecture & Répartition des Rôles

Le Lab 5 finalise le cycle DevOps complet de l'application **Event Manager API** en connectant les tests d'intégration, un frontend conteneurisé, l'orchestration multi-conteneurs avec Docker Compose et un pipeline automatisé CI/CD avec GitHub Actions :

| Partenaire / Rôle | Branche Assignée | Responsabilités Principales |
| :--- | :--- | :--- |
| **Student A (Backend Specialist)** | `feature/backend-cors` | Rédiger la suite de tests d'intégration (`tests/test_integration.py`) et configurer le middleware CORS (`CORSMiddleware`) dans `app/main.py`. |
| **Student B (Frontend Specialist)** | `feature/frontend` | Concevoir l'interface web légère (`frontend/index.html`) avec l'API standard `fetch()` et conteneuriser le serveur web statique (`frontend/Dockerfile`). |
| **Intégration Conjointe (DevOps Pipeline)** | `main` | Assembler la stack complète dans `docker-compose.yml` et configurer le pipeline GitHub Actions (`.github/workflows/devops-pipeline.yml`). |

```
                                AUTOMATED CI/CD PIPELINE FLOW
                              (.github/workflows/devops-pipeline.yml)
+------------------------+        +---------------------------+        +-----------------------------+
|   1. Developer Push    |        |     2. Job: test          |        |     3. Job: build-push      |
|  git push origin main  | -----> |  - Set up Python 3.10     | -----> |  (needs: test)              |
|  or PR to main branch  |        |  - Install dependencies   |        |  - Build & Push Backend     |
|                        |        |  - Run pytest (Unit+Integ)|        |  - Build & Push Frontend    |
+------------------------+        +---------------------------+        +-----------------------------+
```

---

## 2. Phase 1 : Tests d'Intégration API & Baseline CI Backend

### Task 1.1 : Suite de Tests d'Intégration API (`tests/test_integration.py`)
Fichier situé dans [`tests/test_integration.py`](file:///c:/Users/LAPTOP/Documents/DO/EventManager-Pair11/tests/test_integration.py) :

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Participant, Event, Registration

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_test_integration_data():
    """Garantit l'idempotence des tests en nettoyant les données créées."""
    def _cleanup():
        db = SessionLocal()
        try:
            db.query(Registration).delete()
            db.query(Participant).filter(Participant.email == "alice@example.com").delete()
            db.query(Event).filter(Event.title.in_(["DevOps Integration Conf", "Cybersecurity Workshop"])).delete()
            db.commit()
        finally:
            db.close()

    _cleanup()
    yield
    _cleanup()


# Integration Test 1: Event Creation & Persistence Verification
def test_create_and_fetch_event_integration():
    response = client.post("/events/", json={
        "title": "DevOps Integration Conf",
        "location": "Constantine",
        "date": "2026-12-01",
        "capacity": 200
    })
    assert response.status_code == 201
    event_id = response.json()["id"]
    get_resp = client.get(f"/events/{event_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "DevOps Integration Conf"


# Integration Test 2: Participant Registration & Event Sign-up Workflow
def test_register_participant_to_event_integration():
    # 1. Create Event
    e_resp = client.post("/events/", json={
        "title": "Cybersecurity Workshop",
        "location": "NTIC",
        "date": "2026-11-15",
        "capacity": 50
    })
    assert e_resp.status_code == 201
    event_id = e_resp.json()["id"]

    # 2. Create Participant
    p_resp = client.post("/participants/", json={
        "name": "Alice Dev",
        "email": "alice@example.com"
    })
    assert p_resp.status_code == 201
    part_id = p_resp.json()["id"]

    # 3. Register Participant to Event
    reg_resp = client.post(f"/events/{event_id}/register/{part_id}")
    assert reg_resp.status_code in [200, 201]

    # 4. Verify Registration via Event Attendees List
    list_resp = client.get(f"/events/{event_id}/participants")
    assert list_resp.status_code == 200
    assert any(p["id"] == part_id for p in list_resp.json())


# Integration Test 3: Edge Case - Registering to Non-Existent Event
def test_register_non_existent_event_returns_404():
    response = client.post("/events/9999/register/1")
    assert response.status_code == 404
```

### Task 1.2 : Configuration des Secrets & Workflow CI Initial
1. Dans GitHub : **Repository Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions** $\rightarrow$ **New repository secret** :
   - `DOCKER_HUB_USERNAME` : votre nom d'utilisateur Docker Hub.
   - `DOCKER_HUB_TOKEN` : un Personal Access Token (PAT) généré depuis [Docker Hub Security Settings](https://hub.docker.com/settings/security).

---

## 3. Réponses aux Questions de Réflexion — Section 1

### **Q1.1 : How do integration tests (using TestClient) differ from unit tests written in Lab 2 in terms of subsystem interaction and database verification?**

> **Réponse :**
> - **Périmètre et Isolation (Scope) :** Les tests unitaires du Lab 2 isolaient chaque fonction métier ou chaque routeur indépendamment, souvent en simulant (*mocking*) les dépendances externes ou en testant des fonctions pures. À l'inverse, les tests d'intégration avec `TestClient` traversent l'ensemble de la pile applicative : middleware HTTP, sérialisation et validation Pydantic, résolution des routes FastAPI, injection de dépendances (`Depends(get_db)`), et exécution réelle des requêtes ORM SQLAlchemy.
> - **Interaction des Sous-Systèmes :** Un test d'intégration valide la coopération de plusieurs sous-systèmes distincts (par exemple, créer un participant, créer un événement, puis créer une relation d'inscription entre les deux via des clés étrangères).
> - **Vérification de la Base de Données :** Les tests unitaires vérifient la logique d'une fonction isolée. Les tests d'intégration vérifient la persistance réelle des données, le respect des contraintes relationnelles SQL (`UNIQUE`, `NOT NULL`, `FOREIGN KEY`), la validité des transactions ACID (`db.commit()`, `db.refresh()`) et l'intégrité référentielle en interrogeant la base via des requêtes successives (`POST` puis `GET`).

### **Q1.2 : Explain the role of the `needs: test` directive in the GitHub Actions workflow. What happens to the image build job if an integration test fails?**

> **Réponse :**
> - **Rôle de la directive `needs: test` :** Cette directive établit une dépendance séquentielle stricte (Directed Acyclic Graph) entre les jobs du workflow. Elle force le job `build-and-push` à attendre la fin complète et le succès explicite du job `test`.
> - **Conséquence en cas d'échec d'un test :** Si un test unitaire ou d'intégration échoue (code de sortie non nul renvoyé par `pytest`), le statut du job `test` passe en `FAILED`. En conséquence, le job `build-and-push` est automatiquement **annulé / ignoré (SKIPPED)**. Cela implémente le principe fondamental du **Quality Gate** en DevOps : aucune image Docker défectueuse ou contenant un bug de régression ne peut être construite ni poussée vers le registre Docker Hub.

---

## 4. Phase 2 : Feature Branching & Développement des Composants

### Task 2.1 : Student A — Configuration du Middleware CORS (`feature/backend-cors`)
Commandes Git pour Student A :
```bash
git checkout -b feature/backend-cors
```

Modification de [`app/main.py`](file:///c:/Users/LAPTOP/Documents/DO/EventManager-Pair11/app/main.py) :
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import events, participants, registrations


app = FastAPI(
    title="Event Manager API",
    description="A teaching project for Git, Docker and CI/CD",
    version="1.0.0"
)

# Configuration CORS pour autoriser l'accès depuis le conteneur Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Origines autorisées en développement
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(events.router)
app.include_router(participants.router)
app.include_router(registrations.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to Event Manager API"
    }
```

Commit & Push :
```bash
git add app/main.py
git commit -m "feat(backend): configure FastAPI CORSMiddleware for frontend access"
git push -u origin feature/backend-cors
```

---

### Task 2.2 : Student B — Interface Web Minimale & Conteneur Frontend (`feature/frontend`)
Commandes Git pour Student B :
```bash
git checkout -b feature/frontend
```

1. Fichier [`frontend/index.html`](file:///c:/Users/LAPTOP/Documents/DO/EventManager-Pair11/frontend/index.html) :
```html
<!DOCTYPE html>
<html>
<head><title>Event Manager</title></head>
<body>
<h1>Event Manager UI</h1>
<button onclick="loadEvents()">Fetch Events</button>
<ul id="eventList"></ul>
<script>
async function loadEvents() {
  const res = await fetch('http://localhost:8000/events/');
  const events = await res.json();
  document.getElementById('eventList').innerHTML =
    events.map(e => `<li>${e.title} - ${e.location}</li>`).join('');
}
</script>
</body>
</html>
```

2. Fichier [`frontend/Dockerfile`](file:///c:/Users/LAPTOP/Documents/DO/EventManager-Pair11/frontend/Dockerfile) :
```dockerfile
# frontend/Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY ./index.html .
EXPOSE 80
CMD ["python", "-m", "http.server", "80"]
```

Commit & Push :
```bash
git add frontend/
git commit -m "feat(frontend): create minimal UI and static server Dockerfile"
git push -u origin feature/frontend
```

---

## 5. Réponses aux Questions de Réflexion — Section 2

### **Q2.1 : Why does a web browser block frontend API requests to http://localhost:8000 if CORS middleware is missing on the backend?**

> **Réponse :**
> - **Politique de Même Origine (Same-Origin Policy - SOP) :** Les navigateurs web modernes implémentent la SOP comme mesure de sécurité fondamentale pour empêcher un script exécuté sur une origine d'accéder sans restriction aux données d'une autre origine. Une origine est définie par le triplet `(protocole, hôte, port)`.
> - **Différence d'Origines :** Ici, le frontend est servi depuis `http://localhost:80` (port 80) alors que l'API backend écoute sur `http://localhost:8000` (port 8000). Comme les ports diffèrent, il s'agit d'une requête inter-origines (*Cross-Origin*).
> - **Rôle du Middleware CORS :** Lorsque le frontend exécute `fetch("http://localhost:8000/events/")`, le navigateur vérifie la présence des en-têtes HTTP de réponse CORS (comme `Access-Control-Allow-Origin`). Si le backend n'a pas de middleware CORS configuré, ces en-têtes sont absents : le navigateur bloque alors la lecture de la réponse par le code JavaScript pour des raisons de sécurité.

---

## 6. Phase 3 : Intégration Multi-Conteneurs & Pipeline CI/CD Étendu

### Task 3.1 : Pull Requests & Fusion dans `main`
1. Ouvrir une Pull Request pour `feature/backend-cors` $\rightarrow$ `main`.
2. Ouvrir une Pull Request pour `feature/frontend` $\rightarrow$ `main`.
3. Réviser le code et fusionner les deux branches dans `main`.

---

### Task 3.2 : Orchestration Multi-Conteneurs (`docker-compose.yml`)
Fichier [`docker-compose.yml`](file:///c:/Users/LAPTOP/Documents/DO/EventManager-Pair11/docker-compose.yml) à la racine du dépôt :

```yaml
version: '3.8'

services:
  backend:
    build: .
    container_name: eventmanager_backend
    ports:
      - "8000:8000"
    volumes:
      - events_sqlite_data:/app

  frontend:
    build: ./frontend
    container_name: eventmanager_frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  events_sqlite_data:
```

---

### Task 3.3 : Extension du Pipeline CI/CD (`.github/workflows/devops-pipeline.yml`)
Fichier [`.github/workflows/devops-pipeline.yml`](file:///c:/Users/LAPTOP/Documents/DO/EventManager-Pair11/.github/workflows/devops-pipeline.yml) :

```yaml
name: Event Manager CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python 3.10
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run Unit & Integration Tests
        run: pytest

  build-and-push-backend:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Log in to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_HUB_USERNAME }}
          password: ${{ secrets.DOCKER_HUB_TOKEN }}
      - name: Build & Push Backend Image
        uses: docker/build-push-action@v4
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: ${{ secrets.DOCKER_HUB_USERNAME }}/eventmanager-backend:latest

  build-and-push-frontend:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Log in to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_HUB_USERNAME }}
          password: ${{ secrets.DOCKER_HUB_TOKEN }}
      - name: Build & Push Frontend Image
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          file: ./frontend/Dockerfile
          push: true
          tags: ${{ secrets.DOCKER_HUB_USERNAME }}/eventmanager-frontend:latest
```

---

### Task 3.4 : Vérification Locale et Exécution du Pipeline
1. Lancer la pile multi-conteneurs localement :
   ```bash
   docker compose up --build -d
   ```
2. Ouvrir `http://localhost` dans le navigateur et cliquer sur le bouton **"Fetch Events"**.
3. Confirmer que la liste des événements s'affiche correctement sans erreur dans la console devtools (`F12`).
4. Pousser la branche `main` fusionnée vers GitHub :
   ```bash
   git add .
   git commit -m "feat(devops): multi-container compose and dual-image CI/CD pipeline"
   git push origin main
   ```
5. Aller dans l'onglet **Actions** de votre dépôt GitHub pour observer l'exécution verte du pipeline :
   - `test` $\rightarrow$ Réussite (49 tests passés avec succès).
   - `build-and-push-backend` $\rightarrow$ Image envoyée sur Docker Hub.
   - `build-and-push-frontend` $\rightarrow$ Image envoyée sur Docker Hub.

---

## 7. Réponses aux Questions de Réflexion — Section 3

### **Q3.1 : How does Docker Compose enable internal network communication between containers defined in the same docker-compose.yml file?**

> **Réponse :**
> - **Création automatique d'un réseau dédié :** Par défaut, Docker Compose crée automatiquement un réseau de type bridge utilisateur (nommé `<projet>_default`) et y connecte tous les conteneurs déclarés dans la section `services`.
> - **Résolution DNS interne (Service Discovery) :** Docker intègre un résolveur DNS interne (`127.0.0.11`). Le nom de chaque service (ex: `backend`, `frontend`) sert d'alias DNS accessible pour les autres conteneurs du même réseau. Un conteneur peut ainsi joindre le backend directement via son nom de service (ex: `http://backend:8000`) sans avoir besoin de connaître son adresse IP dynamique interne.

### **Q3.2 : Why is executing both unit and integration tests inside an automated CI pipeline critical before building and pushing container images to a registry?**

> **Réponse :**
> - **Non-Régression et Intégrité Globale :** Les tests unitaires vérifient la logique fine et isolée, tandis que les tests d'intégration valident la persistance des données, la compatibilité des schémas ORM et l'interopérabilité des routes HTTP. Exécuter les deux garantit qu'aucun composant unitaire ni aucune interaction inter-services n'est cassé.
> - **Prévention de la Pollution du Registre (Docker Hub) :** Construire et pousser une image Docker est coûteux en temps, en bande passante et en stockage. Si une image est poussée avec un bug, les environnements de staging ou de production qui tirent le tag `:latest` risquent de déployer un artefact défaillant, provoquant des pannes d'infrastructure.
> - **Principe DevOps du "Fail Fast" :** Le pipeline échoue immédiatement à l'étape des tests en quelques secondes, fournissant un retour immédiat aux développeurs avant que toute action irréversible de publication ne soit engagée.

