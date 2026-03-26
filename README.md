# Algo Trading System (Hybrid: Python + Spring Boot + Angular)

## Services
- algo-python (FastAPI strategy engine)
- algo-backend (Spring Boot + PostgreSQL)
- algo-ui (Angular dashboard)

## Quick Start

### 1) Postgres
Create DB:
```
CREATE DATABASE algo;
```

### 2) Backend
```
cd algo-backend
mvn spring-boot:run
```

### 3) Python
```
cd algo-python
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 4) Angular
```
cd algo-ui
npm install
ng serve
```

Open: http://localhost:4200

## Flow
Python -> Strategy -> Signal -> Spring Boot -> DB -> Angular UI
