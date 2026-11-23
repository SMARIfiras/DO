# Lab 6: Kubernetes Container Orchestration & Continuous Deployment (CD)
## Technical Solution Report & Deployment Guide (Pair Assignment)

**Institution:** Université Abdelhamid Mehri - Constantine 2 • Faculté des NTIC  
**Specialty:** 5th Year Cybersecurity Engineering (Cybersecurity Engineers)  
**Module:** DevOps  
**Pair:** Student A (**SMARI Firas** - `smrfiras1`) & Student B (`soheib2004`)  
**Application Stack:** FastAPI (Backend), Nginx (Frontend), SQLite (Storage), Docker Desktop Kubernetes (K8s)

---

## 1. Roles & Architecture Overview

In this lab, Student A (Backend Specialist) and Student B (Frontend Specialist) orchestrate the Event Manager application on a local single-node Kubernetes cluster and automate deployment using a self-hosted CI/CD runner.

| Partner / Role | Assigned Branch | Target Files | Core Responsibilities |
|---|---|---|---|
| **Student A (Backend Specialist)** | `feature/k8s-backend` | • `k8s/events-pvc.yaml`<br>• `k8s/backend-deployment.yaml`<br>• `k8s/backend-service.yaml` | Construct SQLite PersistentVolumeClaim, Backend Deployment (probes, non-root security context, PVC mount), and ClusterIP Service. |
| **Student B (Frontend Specialist)** | `feature/k8s-frontend` | • `k8s/frontend-deployment.yaml`<br>• `k8s/frontend-service.yaml` | Construct Frontend Deployment and LoadBalancer Service (binding to `localhost:80`). |
| **Joint Pair (DevOps Pipeline)** | `main` | • `.github/workflows/devops-pipeline.yml` | Merge PRs, verify cluster primitives, test self-healing & rolling updates, teardown resources, and setup CD pipeline. |

```
                                KUBERNETES CLUSTER ARCHITECTURE
               +---------------------------------------------------------------+
               |                 Docker Desktop Kubernetes Cluster             |
               |                                                               |
  Browser      |   +-----------------------+       +-----------------------+   |
(localhost:80) |   |    frontend-service   |       |    backend-service    |   |
 ------------> |   |      LoadBalancer     |       |       ClusterIP       |   |
               |   |       (Port 80)       |       |      (Port 8000)      |   |
               |   +-----------+-----------+       +-----------+-----------+   |
               |               |                               ^               |
               |               v                               | (Internal DNS)|
               |   +-----------+-----------+       +-----------+-----------+   |
               |   |  frontend-deployment  | ----> |  backend-deployment   |   |
               |   |     (2 Pod Replicas)  |       |    (2 Pod Replicas)   |   |
               |   +-----------------------+       +-----------+-----------+   |
               |                                               |               |
               |                                               v               |
               |                                   +-----------+-----------+   |
               |                                   |  sqlite-pvc (1Gi RWO) |   |
               |                                   |    (/app/data mount)  |   |
               |                                   +-----------------------+   |
               +---------------------------------------------------------------+
```

---

## 2. Environment Setup & Storage Specifications

### Task 1.1: Enable Built-in Kubernetes & Inspect Cluster

1. Open **Docker Desktop** → **Settings (Gear icon)** → **Kubernetes**.
2. Check **Enable Kubernetes** and click **Apply & restart**.
3. Verify cluster connectivity in PowerShell:

```powershell
kubectl cluster-info
kubectl get nodes -o wide
kubectl describe node docker-desktop
```

*Expected Output:* The control-plane status displays as `Ready`, running Kubernetes on `docker-desktop`.

---

### Task 1.2: Persistent Storage Manifest (`k8s/events-pvc.yaml`)

Because SQLite writes state to disk, we define a `PersistentVolumeClaim` (PVC) requesting 1Gi of storage with `ReadWriteOnce` access mode.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: sqlite-pvc
  labels:
    app: backend
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

---

## 3. Deployment Manifest Specifications

### Task 2.1: Student A — Backend Deployment (`k8s/backend-deployment.yaml`)

Branch: `feature/k8s-backend`

This manifest adheres strictly to enterprise and cybersecurity standards:
- **Security Context**: `runAsNonRoot: true`, `runAsUser: 1000` (prevents privilege escalation).
- **Probes**: Configured with `livenessProbe` and `readinessProbe` to guarantee zero-downtime traffic routing.
- **Volume Mount**: Mounts `sqlite-pvc` to `/app/data`.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deployment
  labels:
    app: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: backend
          image: smrfiras1/eventmanager-backend:latest
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8000
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
          env:
            - name: DATABASE_URL
              value: "sqlite:////app/data/events.db"
          livenessProbe:
            httpGet:
              path: /events/
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /events/
              port: 8000
            initialDelaySeconds: 3
            periodSeconds: 5
          volumeMounts:
            - name: sqlite-storage
              mountPath: /app/data
      volumes:
        - name: sqlite-storage
          persistentVolumeClaim:
            claimName: sqlite-pvc
```

---

### Task 2.2: Student B — Frontend Deployment (`k8s/frontend-deployment.yaml`)

Branch: `feature/k8s-frontend`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-deployment
  labels:
    app: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: frontend
          image: smrfiras1/eventmanager-frontend:latest
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 80
```

---

## 4. Apply & Inspect Deployments and Pods

Apply the storage and deployment manifests to the cluster:

```powershell
kubectl apply -f k8s/events-pvc.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
```

Inspect workload statuses:

```powershell
kubectl get deployments
kubectl get pods -o wide
kubectl describe pod -l app=backend
```

*Verification Criterion:* All pods transition to `STATUS: Running` and `READY: 1/1`.

---

## 5. Expose the Application Using Services

### Task 4.1: Backend Service (`k8s/backend-service.yaml`)

Constructed as `ClusterIP` to restrict backend access exclusively to internal cluster workloads:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  labels:
    app: backend
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
    - name: http
      protocol: TCP
      port: 8000
      targetPort: 8000
```

### Task 4.2: Frontend Service (`k8s/frontend-service.yaml`)

Constructed as `LoadBalancer` which Docker Desktop automatically binds to host `localhost:80`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  labels:
    app: frontend
spec:
  type: LoadBalancer
  selector:
    app: frontend
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 80
```

---

## 6. Apply & Inspect Services & Networking

Apply service manifests:

```powershell
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/frontend-service.yaml
kubectl get svc
kubectl describe svc backend-service
```

### Cross-Pod Internal DNS Verification:
Execute a request from a frontend pod to verify service discovery via CoreDNS:

```powershell
# In PowerShell:
$FRONTEND_POD = (kubectl get pod -l app=frontend -o jsonpath="{.items[0].metadata.name}")
kubectl exec -it $FRONTEND_POD -- curl http://backend-service:8000/events/
```

*Verification:* Open `http://localhost` in the browser to verify the frontend interface.

---

## 7. Self-Healing & Data Persistence Verification

1. **Insert data**: Create a new event via the UI or directly via port-forward / curl.
2. **Simulate pod failure**:
   ```powershell
   kubectl delete pod -l app=backend --force
   ```
3. **Observe self-healing**:
   ```powershell
   kubectl get pods -w
   ```
   *Observation:* The ReplicaSet immediately launches replacement pods to restore the desired state of 2 replicas.
4. **Verify data persistence**: Refresh `http://localhost`. The records persist because the SQLite database file resides on the mounted `sqlite-pvc`.

---

## 8. Horizontal Scaling & Zero-Downtime Rolling Updates

### Scaling Backend Replicas:
```powershell
kubectl scale deployment backend-deployment --replicas=4
kubectl get pods -l app=backend
kubectl describe svc backend-service
```
*Observation:* The `Endpoints` field of `backend-service` dynamically updates to list 4 pod IP addresses.

### Zero-Downtime Rolling Update:
```powershell
kubectl set image deployment/backend-deployment backend=smrfiras1/eventmanager-backend:v2
kubectl rollout status deployment/backend-deployment
kubectl rollout history deployment/backend-deployment
```

---

## 9. Teardown & Cleanup

To cleanly remove all resources:
```powershell
kubectl delete -f k8s/
kubectl get pods,svc,pvc
```

---

## 10. Continuous Deployment Pipeline (`.github/workflows/devops-pipeline.yml`)

The GitHub Actions workflow includes automated Continuous Deployment running on a self-hosted runner:

```yaml
  deploy:
    needs: [build-and-push-backend, build-and-push-frontend]
    runs-on: self-hosted
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3

      - name: Dry-Run Check
        run: kubectl apply --dry-run=client -f k8s/

      - name: Apply Manifests
        run: kubectl apply -f k8s/

      - name: Rollout Restart
        run: |
          kubectl rollout restart deployment/backend-deployment
          kubectl rollout restart deployment/frontend-deployment

      - name: Rollout Verification
        run: |
          kubectl rollout status deployment/backend-deployment
          kubectl rollout status deployment/frontend-deployment
```

---

## 11. Lab Reflection & Security Questions

### Q1.1 (Storage & State)
> **Why is a PersistentVolumeClaim (PVC) necessary in Kubernetes when using SQLite, whereas standard container restarts lose internal state? How does PVC binding differ from local volume mounts in Docker Compose?**

- **Root Cause of Data Loss Without PVC:** Pod filesystems in Kubernetes are ephemeral. Each container runs with a temporary read-write layer managed by the container runtime (`containerd` / `overlay2`). When a pod crashes, is evicted, or is replaced during a rolling update, its ephemeral container layer is permanently deleted along with any internal database file.
- **Role of PVC:** A PersistentVolumeClaim abstracts the request for persistent underlying storage. By attaching `sqlite-pvc` to `/app/data`, Kubernetes mounts persistent storage outside the pod's lifecycle. When the ReplicaSet replaces a pod, the new pod re-attaches the existing PersistentVolume, ensuring zero data loss.
- **PVC vs Docker Compose Mounts:** Docker Compose local volume mounts bind directly to host directory paths on a single machine. In Kubernetes, PVCs decouple the storage request (Claim) from the actual storage implementation (PersistentVolume / StorageClass), enabling portability, dynamic provisioning, access mode enforcement (`ReadWriteOnce`, `ReadWriteMany`), and cloud storage orchestration across multi-node clusters.

---

### Q1.2 (Service Abstraction)
> **Explain the difference between ClusterIP and LoadBalancer service types. Why is backend-service configured as ClusterIP while frontend-service uses LoadBalancer?**

- **ClusterIP:** Allocates a virtual, non-routable IP address accessible **only from within the Kubernetes cluster**. CoreDNS registers its name (e.g., `backend-service:8000`), allowing internal pods to communicate with it.
- **LoadBalancer:** Requests an external load balancer from the cloud provider (or binds directly to host interfaces like `localhost` in Docker Desktop) to route public external internet traffic into the cluster.
- **Architectural Rationale:** Following the **Principle of Least Privilege** and defense-in-depth, the database and API backend should not be publicly exposed to the external internet. Only the frontend web server requires public exposure (`LoadBalancer` on port 80). The frontend communicates with the backend privately inside the cluster via `ClusterIP`.

---

### Q2.1 (Health & Reliability)
> **Differentiate between a livenessProbe and a readinessProbe in Kubernetes. What occurs if a readiness probe fails during a rolling update deployment?**

- **Liveness Probe (`livenessProbe`):** Monitors if the container is still alive and operational. If it fails consecutively past `failureThreshold`, the kubelet kills the container and initiates a restart according to the `restartPolicy`.
- **Readiness Probe (`readinessProbe`):** Determines whether the container is ready to accept incoming user network traffic. If it fails, the kubelet removes the pod's IP address from the corresponding Service `Endpoints`, stopping traffic from hitting the unhealthy pod.
- **Impact during a Rolling Update:** If a new pod version fails its readiness probe during a rolling update (`kubectl set image`), Kubernetes marks the pod as `NotReady` and refuses to route traffic to it. Because the new pod never reaches the ready state, the deployment controller **halts the rollout**, preventing healthy old pods from being terminated. This prevents deployment bugs from causing user-facing downtime.

---

### Q3.1 (Security Context)
> **Explain the cybersecurity benefits of configuring `runAsNonRoot: true` and `runAsUser: 1000` inside container pod specifications in production Kubernetes clusters.**

- **Mitigation of Container Breakout / Privilege Escalation:** By default, containers execute processes as UID 0 (`root`). If an attacker exploits a vulnerability in the application (such as an arbitrary code execution or SQLite injection), they gain root privileges inside the container.
- **Kernel Namespace Isolation:** The Linux kernel shares the host kernel with containers. If an attacker with container root privileges exploits a kernel privilege escalation vulnerability (e.g., dirty COW) or accesses host volume mounts, they can break out of the container boundary and compromise the host system.
- **Enforcement of Non-Root User:** Configuring `runAsNonRoot: true` instructs the container runtime to strictly reject image execution if it attempts to start as root (UID 0). `runAsUser: 1000` forces the application process to execute under a dedicated unprivileged user, adhering strictly to the principle of least privilege.

---

### Q3.2 (Continuous Deployment)
> **Why does executing the deployment job on a self-hosted runner allow direct management of a local Docker Desktop Kubernetes cluster compared to GitHub cloud runners?**

- **Network Boundary & Firewall Isolation:** A local Docker Desktop Kubernetes cluster runs on the student laptop behind a Network Address Translation (NAT) router and local firewall with private RFC 1918 IP addresses (`127.0.0.1` / `localhost`).
- **Cloud Runner Limitation:** Standard GitHub-hosted runners execute in GitHub's public cloud datacenters (Azure). They have zero network route or visibility into private localhost networks and cannot reach the local Kubernetes API server (`https://127.0.0.1:6443`).
- **Self-Hosted Runner Advantage:** A self-hosted runner executes natively on the student's local operating system. Because it runs on the same machine, it has direct authenticated access to the local `kubeconfig` (`~/.kube/config`), allowing `kubectl` commands to communicate directly with the local Docker Desktop cluster without exposing cluster ports to the public internet.

