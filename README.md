# Library Management System API

The Library Management System API is a backend for tracking the books a library lends and the members who borrow them. Library staff can create, view, update, and delete both resources, and every book is associated with exactly one member.

This is Assignment 1 for SDEV 3310. It covers Modules 1-4: API basics, REST and CRUD, Pydantic validation, and OpenAPI design.

## Scope

Books and Members are stored in Python lists while the application is running, so all data disappears when the server restarts. This is intentional. The assignment is due before the persistence module, so Assignment 2 will replace the in-memory collections with SQLAlchemy and a relational database.

## Requirements

- [uv](https://docs.astral.sh/uv/)

`uv` manages the Python version, the virtual environment, and the project dependencies.

### Install uv

macOS and Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart your terminal, then verify the installation:

```bash
uv --version
```

### Set up the project

From the repository root, run:

```bash
uv sync
```

If the required Python version is unavailable, `uv sync` downloads it. It also creates the virtual environment and installs the dependencies recorded in `uv.lock`.

## Run the API

```bash
uv run uvicorn app.main:app --reload
```

The development server will be available at `http://localhost:8000`.

## Explore the API

The application exposes three views of the same OpenAPI contract:

- `http://localhost:8000/docs` — Swagger UI for exploring and calling endpoints
- `http://localhost:8000/redoc` — ReDoc for reading reference documentation
- `http://localhost:8000/openapi.json` — the machine-readable OpenAPI document

| Method | URL | CRUD operation | Successful status |
|---|---|---|---|
| `GET` | `/` | Read API introduction | `200 OK` |
| `GET` | `/health` | Read API health | `200 OK` |
| `GET` | `/members` | Read all Members | `200 OK` |
| `GET` | `/members/{member_id}` | Read one Member | `200 OK` |
| `POST` | `/members` | Create a Member | `201 Created` |
| `PUT` | `/members/{member_id}` | Update a Member | `200 OK` |
| `DELETE` | `/members/{member_id}` | Delete a Member | `204 No Content` |
| `GET` | `/members/{member_id}/books` | Read one Member's Books | `200 OK` |
| `GET` | `/books` | Read all Books | `200 OK` |
| `GET` | `/books/{book_id}` | Read one Book | `200 OK` |
| `POST` | `/books` | Create a Book | `201 Created` |
| `PUT` | `/books/{book_id}` | Update a Book | `200 OK` |
| `DELETE` | `/books/{book_id}` | Delete a Book | `204 No Content` |

## Members

Use this JSON body with `POST /members` and `PUT /members/{member_id}`:

```json
{
  "name": "Grace Hopper",
  "email": "grace.hopper@example.com",
  "membership_id": "LIB-000002",
  "phone": "555-010-9876"
}
```

Member validation rules:

- `name` is required and must contain 1-120 characters.
- `email` is required and must be a valid email address.
- `membership_id` is required and must contain 1-32 characters.
- `phone` is required and must be a ten-digit North American number. The separators people normally type are allowed, along with an optional `+1` country code, so `5550109876`, `555-010-9876`, `(555) 010-9876`, and `+1 555.010.9876` are all accepted. `12345` and `555-010-987` are rejected.
- Surrounding whitespace is removed before validation.
- Unexpected fields are rejected.

`email` and `membership_id` must also be unique across all members. A request that reuses either value returns `409 Conflict`. Email addresses are compared without regard to case, so `Grace@example.com` conflicts with `grace@example.com`.

## Books

Use this JSON body with `POST /books` and `PUT /books/{book_id}`:

```json
{
  "title": "The Pragmatic Programmer",
  "author": "Andrew Hunt",
  "isbn": "978-0-201-61622-4",
  "published_year": 1999,
  "member_id": 1
}
```

Book validation rules:

- `title` is required and must contain 1-200 characters.
- `author` is required and must contain 1-120 characters.
- `isbn` is required and must contain 1-20 characters. No format is enforced, so ISBN-10 and ISBN-13 are both accepted, with or without hyphens.
- `published_year` is required and must fall between 1450 and the current year.
- `member_id` is required and must be greater than zero.
- Surrounding whitespace is removed before validation.
- Unexpected fields are rejected.

`isbn` must also be unique across all books, so a request that reuses one returns `409 Conflict`.

## The Member-Book relationship

Each Book is borrowed by exactly one Member, and a Member may borrow many Books. `Book.member_id` is the child-side reference that records the relationship.

- Creating or updating a Book whose `member_id` does not match an existing Member returns `404 Not Found`.
- `GET /members/{member_id}/books` returns every Book borrowed by one Member. A Member who has borrowed nothing returns an empty list, while a Member who does not exist returns `404 Not Found`.
- Deleting a Member who still has Books returns `409 Conflict`. Delete those Books first, or reassign them by sending a different `member_id` in `PUT /books/{book_id}`.

### Example: create a Member, then a Book they borrowed

```bash
curl -X POST http://localhost:8000/members \
  -H "Content-Type: application/json" \
  -d '{
        "name": "Grace Hopper",
        "email": "grace.hopper@example.com",
        "membership_id": "LIB-000002",
        "phone": "555-010-9876"
      }'
```

The response contains the generated `id`. Pass it as `member_id` when recording the Book:

```bash
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -d '{
        "title": "Structure and Interpretation of Computer Programs",
        "author": "Harold Abelson",
        "isbn": "978-0-262-51087-5",
        "published_year": 1985,
        "member_id": 2
      }'
```

Then read that Member's Books:

```bash
curl http://localhost:8000/members/2/books
```

## Try a validation error

Send this request to `POST /members`:

```json
{
  "name": "",
  "email": "not-an-email",
  "membership_id": "LIB-000009",
  "phone": "12345",
  "nickname": "Unexpected field"
}
```

FastAPI returns `422 Unprocessable Content`. The response identifies where each error occurred, which rule failed, and which value was rejected. The route function does not run when request validation fails.

## Status codes

| Status | When it is returned |
|---|---|
| `200 OK` | A successful read or update |
| `201 Created` | A successful create |
| `204 No Content` | A successful delete, which has no response body |
| `404 Not Found` | The requested Book or Member, or a referenced Member, does not exist |
| `409 Conflict` | A duplicate ISBN, email, or membership ID, or a Member who still has Books |
| `422 Unprocessable Content` | The request body failed Pydantic validation |

Pydantic validates individual field values and returns `422`. Rules that compare a value against the rest of the collection, such as uniqueness and the existence of a referenced Member, are checked by the application and return `409` or `404`.

## Temporary data

Books and Members are stored in Python lists while the application is running, seeded with one Member and one Book so the endpoints return data on a fresh start. Changes disappear when the development server restarts. Assignment 2 replaces this with database persistence.

## Current project structure

```text
assignment-1/
├── app/
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── books.py
│   │   └── members.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── books.py
│   │   └── members.py
│   ├── __init__.py
│   ├── main.py
│   └── storage.py
├── pyproject.toml
├── uv.lock
└── README.md
```

The project uses a layer-first structure. Route handlers live in `app/routers/`, API data contracts live in `app/schemas/`, and the temporary in-memory collections live in `app/storage.py`. Service and repository layers can be added when the course introduces the responsibilities they contain.
