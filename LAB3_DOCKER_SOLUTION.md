# Lab 3: Docker Containerization, Deployment & Named Volume Storage
## Complete Pair Solution: Student A & Student B

**Institution:** Université Abdelhamid Mehri - Constantine 2 • NTIC Faculty  
**Module:** DevOps Engineering — 5th Year Computer Science / Engineering  
**Application Architecture:** FastAPI Event Manager API (FastAPI, SQLAlchemy, SQLite)  
**Pair:** Student A (`SMARIfiras`) & Student B (`soheib2004` / `walidabderrahim`)  

---

## 1. Collaborative Lab Architecture

In this lab, student pairs collaborate through Docker Hub and Docker Compose:
- **Student A (`SMARIfiras`)**: Builds the Docker image from source, verifies container isolation and data destruction, tags the image, and pushes it to Docker Hub.
- **Student B (`soheib2004`)**: Pulls Student A's pre-built image from Docker Hub, configures local orchestration with Docker Compose, mounts a Named Volume, and proves persistence.

```
+-----------------------------------------------------------------------------------+
|                           STUDENT A (SMARIfiras)                                  |
|  1. Write Dockerfile                                                              |
|  2. Build image: eventmanager-app:v1                                              |
|  3. Run Container 1 & verify isolation (Container 2 & ephemeral data loss)        |
|  4. Tag image: smarifiras/eventmanager-api:v1                                     |
|  5. docker push smrfiras1/eventmanager-api:v1                                     |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
                         +-------------------------------+
                         |          Docker Hub           |
                         | smarifiras/eventmanager-api:v1|
                         +-------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                           STUDENT B (soheib2004)                                  |
|  1. docker pull smrfiras1/eventmanager-api:v1                                     |
|  2. Configure docker-compose.yml with Named Volume events_sqlite_data             |
|  3. docker compose up -d                                                          |
|  4. Populate tuples via Swagger UI (http://localhost:8000/docs)                   |
|  5. Test lifecycle persistence: docker compose down && docker compose up -d       |
|  6. Verify all database records remain preserved                                  |
+-----------------------------------------------------------------------------------+
```

---

## SECTION 1: Docker Containerization & Verification

### Task 1.1: Constructing the Dockerfile

The `Dockerfile` is placed in the project root:

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Directive Analysis:
- `FROM python:3.10-slim`: Uses a minimal, Debian-based Python 3.10 runtime to keep the image lightweight (~180MB).
- `WORKDIR /app`: Sets the default execution path inside the container.
- `COPY requirements.txt .`: Copies dependencies before application source to maximize build cache reuse.
- `RUN pip install --no-cache-dir -r requirements.txt`: Installs packages without keeping cache artifacts.
- `COPY ./app ./app`: Copies FastAPI application code into the image.
- `EXPOSE 8000`: Documents the exposed HTTP service port.
- `CMD [...]`: Runs Uvicorn bound to `0.0.0.0:8000`.

---

### Task 1.2: Image Build & Container Verification

#### 1. Build the Docker Image
```powershell
docker build -t eventmanager-app:v1 .
```

#### 2. Verify Created Layers
```powershell
docker images
```
*Expected Output:*
```text
REPOSITORY         TAG       IMAGE ID       CREATED          SIZE
eventmanager-app   v1        a1b2c3d4e5f6   15 seconds ago   182MB
```

#### 3. Launch Container 1
```powershell
docker run -d -p 8000:8000 --name container1 eventmanager-app:v1
```

#### 4. Verification via Swagger UI
- Open: `http://localhost:8000/docs`
- Execute `POST /events/` with:
```json
{
  "title": "DevOps Docker Session",
  "description": "Container verification in Constantine",
  "date": "2026-11-10",
  "location": "Constantine 2",
  "capacity": 100
}
```
*Response: HTTP 201 Created.*

---

### Reflection Questions — Section 1

#### Q1.1: What is the conceptual difference between a Docker Image and a Docker Container?
- **Docker Image**: An immutable, read-only template consisting of stacked layers containing the base operating system, runtime (Python 3.10), system libraries, dependencies, and application source code. It is static and serves as the blueprint (class definition).
- **Docker Container**: A dynamic, runnable instance of a Docker Image. Docker runs it inside isolated Linux namespaces (PID, NET, IPC, MNT, UTS) and attaches a thin read-write container layer (overlay2) on top. It is stateful and behaves as the instantiated runtime object.

#### Q1.2: Why must Uvicorn be bound to `--host 0.0.0.0` inside a container rather than `127.0.0.1`?
- `127.0.0.1` (loopback) restricts socket listening exclusively to the container's private internal loopback adapter. External traffic forwarded by Docker (via `-p 8000:8000`) arrives on the container's virtual Ethernet interface (`eth0`) and is immediately rejected.
- `0.0.0.0` instructs Uvicorn to listen on **all available network interfaces** in the container namespace, allowing forwarded requests from the host and Docker bridge network to be received.

#### Q1.3: Why is `COPY requirements.txt .` placed BEFORE `COPY ./app ./app` in the Dockerfile?
- Docker caches intermediate layers. If a layer and its inputs haven't changed, Docker reuses the cached layer.
- `requirements.txt` changes infrequently, whereas application source code (`./app`) changes frequently.
- By placing `COPY requirements.txt .` and `RUN pip install ...` first, Docker skips reinstalling dependencies whenever only application code changes, reducing subsequent build times from minutes to under 2 seconds.

---

## SECTION 2: Multi-Container Isolation & Ephemeral Storage

### Task 2.1: Running a Second Container Instance

#### 1. Launch Container 2 on Port 8001
```powershell
docker run -d -p 8001:8000 --name container2 eventmanager-app:v1
```

#### 2. Query Container 2
Navigate to `http://localhost:8001/docs` and execute `GET /events/`.

#### 3. Observation
- `GET /events/` on Container 2 returns `[]` (empty list).
- The event tuple created in Container 1 does **NOT** exist in Container 2. Each container has an independent, isolated filesystem layer.

---

### Task 2.2: Container Lifecycle & Data Destruction

#### 1. Stop and Remove Container 1
```powershell
docker stop container1
docker rm container1
```

#### 2. Re-create Container 1 on Port 8000
```powershell
docker run -d -p 8000:8000 --name container1 eventmanager-app:v1
```

#### 3. Verify Data Loss
- Query `GET /events/` on `http://localhost:8000/docs`.
- **Result:** Returns `[]` (empty list).
- The previously inserted SQLite records were completely destroyed upon container deletion.

---

### Reflection Questions — Section 2

#### Q2.1: Explain why Container 2 did not see the data created in Container 1, and why destroying Container 1 resulted in complete data loss. Reference Docker read-write container layers in your answer.
- Each container operates on its own dedicated, ephemeral **Read-Write (R/W) Container Layer** stacked over the shared read-only image layers via the `overlay2` storage driver.
- When Container 1 created `events.db`, the file was written exclusively to Container 1's private R/W layer. Container 2's filesystem is completely isolated and cannot read Container 1's R/W layer.
- When Container 1 was stopped and removed (`docker rm`), Docker permanently deleted its R/W layer from the host disk. Because no external volume was attached, `events.db` was permanently deleted.

#### Q2.2: What is an 'ephemeral container filesystem' and why is it problematic for databases like SQLite?
- An ephemeral container filesystem is temporary storage tied directly to a single container's lifecycle.
- Containers are designed to be disposable (cattle, not pets). In cloud and DevOps environments, containers are routinely destroyed, scaled, or upgraded. Relying on ephemeral storage for an embedded database like SQLite guarantees complete data loss whenever a container is stopped or redeployed.

---

## SECTION 3: Data Persistence with Named Volumes

### Task 3.1: Creating and Attaching a Named Volume

#### Approach 1: Docker CLI
```powershell
docker volume create events_sqlite_data
docker run -d -p 8000:8000 -v events_sqlite_data:/app --name container_vol eventmanager-app:v1
```

#### Approach 2: Docker Compose (`docker-compose.yml`)
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - events_sqlite_data:/app

volumes:
  events_sqlite_data:
```

---

### Task 3.2: Verifying Tuple Persistence across Lifecycle

#### 1. Launch Container Stack
```powershell
docker compose up -d
```

#### 2. Insert Records via Swagger UI (`http://localhost:8000/docs`)
- `POST /events/`:
```json
{
  "title": "Persistent Conference",
  "description": "Validated across compose lifecycles",
  "date": "2026-11-25",
  "location": "Constantine",
  "capacity": 120
}
```
- `POST /participants/`:
```json
{
  "name": "Sarah Smari",
  "email": "sarah@univ-constantine2.dz"
}
```

#### 3. Stop and Purge Stack
```powershell
docker compose down
```
*(Removes containers and networks, preserving named volumes).*

#### 4. Relaunch Stack and Check Data
```powershell
docker compose up -d
```
Execute `GET /events/` and `GET /participants/`:
- **Result:** Both the Event and Participant records remain intact and are successfully retrieved from the database.

---

### Reflection Questions — Section 3

#### Q3.1: Explain how Docker Named Volumes ensure data persistence across container restarts, stops, and rebuilds.
- Named Volumes are directories stored on the host filesystem outside the container's storage driver namespace (`/var/lib/docker/volumes/<volume_name>/_data`).
- When mounted to `/app`, all database read/write operations bypass the container's ephemeral layer and write directly to the host-managed directory.
- Because the volume's lifecycle is completely decoupled from the container, removing or rebuilding the container has zero impact on the stored database file.

#### Q3.2: How do Named Volumes differ from unmounted container layers in terms of storage lifecycle and data management?
| Feature | Unmounted Container Layer | Docker Named Volume |
|---|---|---|
| **Lifecycle** | Tied directly to container (deleted on `docker rm`) | Completely decoupled; persists indefinitely until explicit `docker volume rm` |
| **I/O Performance** | Incurs copy-on-write (CoW) overhead via `overlay2` | Direct native host file system I/O performance |
| **Data Sharing** | Strictly isolated to one container instance | Can be mounted concurrently across multiple containers |
| **Backup & Management** | Difficult to access and back up | Easily inspected (`docker volume inspect`) and backed up |

---

## SECTION 4: Collaborative Deployment via Docker Hub (Pair Work)

This section details the collaborative deployment between **Student A** and **Student B**.

---

### Task 4.1: Student A — Image Tagging & Docker Hub Registry Push

Student A (`SMARIfiras`) publishes the verified image artifact to Docker Hub.

#### Step 1: Log in to Docker Hub
```powershell
docker login -u smrfiras1
```
*(Enter Docker Hub password or Personal Access Token when prompted).*

#### Step 2: Tag the Locally Verified Image
```powershell
# Tag with release version v1
docker tag eventmanager-app:v1 smrfiras1/eventmanager-api:v1

# Tag with latest
docker tag eventmanager-app:v1 smrfiras1/eventmanager-api:latest
```

Verify tagged images:
```powershell
docker images smrfiras1/eventmanager-api
```
*Expected Output:*
```text
REPOSITORY                      TAG       IMAGE ID       SIZE
smarifiras/eventmanager-api     v1        a1b2c3d4e5f6   182MB
smarifiras/eventmanager-api     latest    a1b2c3d4e5f6   182MB
```

#### Step 3: Push Image to Docker Hub
```powershell
docker push smrfiras1/eventmanager-api:v1
docker push smrfiras1/eventmanager-api:latest
```
*Output confirms layer pushes and cryptographic digest generation.*

---

### Task 4.2: Student B — Pulling Remote Image & Deploying with Named Volume

Student B (`soheib2004`) pulls the remote artifact and runs it with persistent storage.

#### Step 1: Pull Student A's Remote Image
```powershell
docker pull smrfiras1/eventmanager-api:v1
```

Verify local availability:
```powershell
docker images smrfiras1/eventmanager-api:v1
```

#### Step 2: Configure `docker-compose.yml` (or `docker-compose.student-b.yml`)
The orchestration configuration for Student B binds the remote image to the persistent volume:

```yaml
version: '3.8'

services:
  web:
    image: ${STUDENT_A_IMAGE:-smrfiras1/eventmanager-api:v1}
    container_name: eventmanager-api-student-b
    ports:
      - "8000:8000"
    volumes:
      - events_sqlite_data:/app
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1

volumes:
  events_sqlite_data:
    name: events_sqlite_data
```

#### Step 3: Launch Stack and Verify Deployment
```powershell
docker compose -f docker-compose.student-b.yml up -d
```
Check status:
```powershell
docker ps
```
*Status: `Up ... 0.0.0.0:8000->8000/tcp (eventmanager-api-student-b)`.*

#### Step 4: Populate Data & Verify Persistence Across Restarts
1. Open Swagger UI at `http://localhost:8000/docs`.
2. Insert an Event and register a Participant.
3. Test teardown:
```powershell
docker compose -f docker-compose.student-b.yml down
docker compose -f docker-compose.student-b.yml up -d
```
4. Query `GET /events/`: The records persist intact!

---

### Reflection Questions — Section 4

#### Q4.1: How does sharing pre-built images via Docker Hub eliminate environment discrepancies ('it works on my machine') between Student A and Student B?
1. **Identical Runtime Environment**: The pre-built image packages the exact Debian base OS, Python 3.10 interpreter, and system C-libraries. Any host OS discrepancies between Student A and Student B (e.g., Windows 10 vs. Windows 11, WSL2 configurations, or missing compiler tools) are completely isolated inside the container.
2. **Pinned Dependency Tree**: Python packages and transitive dependencies are installed at build time. Student B does not execute `pip install`, avoiding upstream version drift, broken package wheels, or proxy network issues.
3. **Reproducible Execution Contract**: Ports, startup commands (`uvicorn`), environment variables, and file structures are immutable in the image. If it runs cleanly on Student A's machine, it is guaranteed to execute identically on Student B's machine.

---

## 5. Summary Pair Checklist

| Requirement | Student A (`SMARIfiras`) | Student B (`soheib2004`) | Status |
|---|:---:|:---:|:---:|
| **Dockerfile Created** | Implemented | Verified | ✅ Complete |
| **Local Image Built (`eventmanager-app:v1`)** | Tested on port 8000 | Tested on port 8000 | ✅ Complete |
| **Multi-Container Isolation Verified** | Tested port 8001 | Verified | ✅ Complete |
| **Ephemeral Data Destruction Observed** | Verified with `docker rm` | Verified | ✅ Complete |
| **Named Volume Configured** | `events_sqlite_data` | `events_sqlite_data` | ✅ Complete |
| **Docker Hub Registry Push (Task 4.1)** | `docker push` executed | Consumed image | ✅ Complete |
| **Docker Hub Registry Pull (Task 4.2)** | Produced artifact | `docker pull` executed | ✅ Complete |
| **Compose Stack & Persistence Proven** | `docker-compose.student-a.yml` | `docker-compose.student-b.yml` | ✅ Complete |
| **Reflection Questions Answered** | Q1.1, Q1.2, Q1.3, Q2.1, Q2.2, Q3.1, Q3.2 | Q4.1 & Deployment Verification | ✅ Complete |
