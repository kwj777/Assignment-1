"""FastAPI application for the Library Management System API."""

from fastapi import FastAPI

from app.routers.books import router as books_router
from app.routers.members import router as members_router

# Tag descriptions organize related operations and explain each resource group
# in Swagger UI and ReDoc.
tags_metadata = [
    {
        "name": "General",
        "description": "Basic application information and health checks.",
    },
    {
        "name": "Members",
        "description": (
            "Register and manage library members and view the books they have "
            "borrowed."
        ),
    },
    {
        "name": "Books",
        "description": "Record and manage books borrowed by library members.",
    },
]

# Create the FastAPI application object that Uvicorn will load and run. This
# metadata also appears in the generated API documentation.
app = FastAPI(
    title="Library Management System API",
    description=(
        "Manage library members and the books they borrow. Each book is "
        "borrowed by exactly one member, and a member may borrow many books."
    ),
    version="0.1.0",
    openapi_tags=tags_metadata,
)

# Keeping resource routes in routers prevents main.py from becoming crowded.
app.include_router(members_router)
app.include_router(books_router)


@app.get("/", tags=["General"], summary="Introduce the API")
def read_root() -> dict[str, str]:
    """Return a short introduction to the API."""
    return {"message": "Library Management System API"}


# The health endpoint gives clients a simple way to confirm the API is running.
@app.get("/health", tags=["General"], summary="Check API health")
def health_check() -> dict[str, str]:
    """Confirm that the API process is running."""
    return {"status": "healthy"}
