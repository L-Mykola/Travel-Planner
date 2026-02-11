# Travel Projects API

Backend application for managing travel projects and places to visit.

Travellers can create projects, add artworks from the Art Institute of Chicago API as places to visit, attach notes, mark places as visited, and automatically complete projects when all places are visited.



## 🚀 Tech Stack

- **FastAPI**
- **SQLAlchemy (2.0)**
- **SQLite**
- **httpx**
- **TTL caching (cachetools)**
- **Docker**



## 📦 Features

### Travel Projects
- Create a project (optionally with places in a single request)
- Update project details
- Delete a project (restricted if any place is visited)
- List projects (with pagination and filtering)
- Get a single project

### Places (within project)
- Add a place (validated via Art Institute API)
- Prevent duplicate external places per project
- Enforce maximum 10 places per project
- Update notes
- Mark as visited / unvisited
- Automatically mark project as `completed` when all places are visited

### Business Rules
- A project must have **1–10 places**
- A place is validated against:
  `GET https://api.artic.edu/api/v1/artworks/{id}`
- Cannot delete a project if at least one place is marked as visited
- Project automatically becomes `completed` when all places are visited
- If a place is unvisited, project becomes `active` again



## 🛠 Installation (Local)

### Create virtual environment

```bash
python -m venv .venv
```
### Activate environment

#### Mac/Linux:

```bash
source .venv/bin/activate
```

#### Windows:

```bash
.venv\Scripts\activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```
### Run the server
```bash
uvicorn app.main:app --reload
```

## Run with Docker

```bash
docker compose up --build
```
## API Overview

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects` | Create project (can include places) |
| GET | `/projects` | List projects (pagination + filter) |
| GET | `/projects/{id}` | Get single project |
| PATCH | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Delete project (restricted if visited places exist) |

### Places

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects/{id}/places` | List project places |
| GET | `/projects/{id}/places/{place_id}` | Get single place |
| POST | `/projects/{id}/places` | Add place (validated via ArtIC) |
| PATCH | `/projects/{id}/places/{place_id}` | Update notes / visited |

## Notes

- SQLite database file (`travel.db`) is created automatically
- No external configuration is required
- Business logic is isolated in the service layer
- Designed for clarity and maintainability