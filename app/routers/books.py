"""HTTP endpoints for the Book resource."""

from fastapi import APIRouter, HTTPException, Response, status

from app.routers.members import find_member
from app.schemas.books import BookCreate, BookResponse, BookUpdate
from app.storage import books

# Books use the same collection and item URL pattern as Members.
router = APIRouter(prefix="/books", tags=["Books"])


def find_book(book_id: int) -> BookResponse:
    """Find one book or return an HTTP 404 error to the client."""
    for book in books:
        if book.id == book_id:
            return book

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Book not found",
    )


def ensure_isbn_is_unique(isbn: str, exclude_book_id: int | None = None) -> None:
    """Reject an ISBN already recorded for another book.

    Pydantic validates one request body on its own, so a rule that compares a
    value against the rest of the collection has to be checked here. Updates
    pass their own ID to exclude_book_id so a book keeps its existing ISBN.
    """
    for book in books:
        if book.id != exclude_book_id and book.isbn == isbn:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another book already uses this ISBN",
            )


# GET /books reads the entire Book collection.
@router.get(
    "",
    response_model=list[BookResponse],
    summary="List all books",
    description="Return every book currently stored by the application.",
)
def list_books() -> list[BookResponse]:
    """Return every book currently stored in memory."""
    return books


# GET /books/{book_id} reads one Book identified by its path parameter.
@router.get(
    "/{book_id}",
    response_model=BookResponse,
    summary="Get one book",
    description="Return the book identified by the path parameter.",
    responses={404: {"description": "Book not found"}},
)
def get_book(book_id: int) -> BookResponse:
    """Return the book with the requested ID."""
    return find_book(book_id)


# A Book can be created only when the Member who borrowed it exists.
@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a book",
    description=(
        "Record a book and associate it with the existing member who borrowed "
        "it. The ISBN must not already belong to another book."
    ),
    responses={
        404: {"description": "Related member not found"},
        409: {"description": "ISBN already in use"},
    },
)
def create_book(data: BookCreate) -> BookResponse:
    """Create a book associated with an existing member."""
    # Pydantic checks that member_id is a positive integer. Confirming that the
    # member actually exists is the application's responsibility.
    find_member(data.member_id)
    ensure_isbn_is_unique(data.isbn)

    next_book_id = max((book.id for book in books), default=0) + 1
    book = BookResponse(id=next_book_id, **data.model_dump())
    books.append(book)
    return book


# PUT replaces the editable values of the Book identified by the URL.
@router.put(
    "/{book_id}",
    response_model=BookResponse,
    summary="Replace a book",
    description=(
        "Replace all editable fields of an existing book. Supplying a different "
        "member_id reassigns the book to that member."
    ),
    responses={
        404: {"description": "Book or related member not found"},
        409: {"description": "ISBN already in use"},
    },
)
def replace_book(book_id: int, data: BookUpdate) -> BookResponse:
    """Replace the editable fields of an existing book."""
    book = find_book(book_id)
    find_member(data.member_id)
    ensure_isbn_is_unique(data.isbn, exclude_book_id=book_id)

    updated_book = BookResponse(id=book_id, **data.model_dump())
    books[books.index(book)] = updated_book
    return updated_book


# A successful DELETE has no response body, so it returns HTTP 204.
@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book",
    description="Delete a book from the library catalog.",
    responses={404: {"description": "Book not found"}},
)
def delete_book(book_id: int) -> Response:
    """Remove a book from the in-memory collection."""
    book = find_book(book_id)
    books.remove(book)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
