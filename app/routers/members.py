"""HTTP endpoints for the Member resource."""

from fastapi import APIRouter, HTTPException, Response, status

from app.schemas.books import BookResponse
from app.schemas.members import MemberCreate, MemberResponse, MemberUpdate
from app.storage import books, members

# Every route in this file begins with /members and appears under the Members
# heading in FastAPI's generated API documentation.
router = APIRouter(prefix="/members", tags=["Members"])


def find_member(member_id: int) -> MemberResponse:
    """Find one member or return an HTTP 404 error to the client."""
    for member in members:
        if member.id == member_id:
            return member

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Member not found",
    )


def ensure_member_is_unique(
    email: str,
    membership_id: str,
    exclude_member_id: int | None = None,
) -> None:
    """Reject an email or membership ID already used by another member.

    Pydantic validates one request body on its own, so a rule that compares a
    value against the rest of the collection has to be checked here.
    Updates pass their own ID to exclude_member_id so a member keeps its values.
    """
    for member in members:
        if member.id == exclude_member_id:
            continue

        # Email addresses are matched without regard to case so that
        # "Ada@example.com" cannot be registered alongside "ada@example.com".
        if member.email.lower() == email.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another member already uses this email address",
            )

        if member.membership_id == membership_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another member already uses this membership ID",
            )


# GET /members reads the entire Member collection.
@router.get(
    "",
    response_model=list[MemberResponse],
    summary="List all members",
    description="Return every member currently stored by the application.",
)
def list_members() -> list[MemberResponse]:
    """Return every member currently stored in memory."""
    return members


# The value inside {member_id} is supplied by the URL path.
@router.get(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Get one member",
    description="Return the member identified by the path parameter.",
    responses={404: {"description": "Member not found"}},
)
def get_member(member_id: int) -> MemberResponse:
    """Return the member with the requested ID."""
    return find_member(member_id)


# POST creates a new resource, so a successful request returns HTTP 201.
@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a member",
    description=(
        "Register a member. The email address and membership ID must not "
        "already belong to another member."
    ),
    responses={409: {"description": "Email or membership ID already in use"}},
)
def create_member(data: MemberCreate) -> MemberResponse:
    """Create a member from a validated JSON request body."""
    ensure_member_is_unique(data.email, data.membership_id)

    # Generate the next ID from the existing in-memory collection.
    next_member_id = max((member.id for member in members), default=0) + 1
    member = MemberResponse(id=next_member_id, **data.model_dump())
    members.append(member)
    return member


# PUT replaces the editable values of the Member identified by the URL.
@router.put(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Replace a member",
    description="Replace all editable fields of an existing member.",
    responses={
        404: {"description": "Member not found"},
        409: {"description": "Email or membership ID already in use"},
    },
)
def replace_member(member_id: int, data: MemberUpdate) -> MemberResponse:
    """Replace the editable fields of an existing member."""
    member = find_member(member_id)
    ensure_member_is_unique(
        data.email,
        data.membership_id,
        exclude_member_id=member_id,
    )

    updated_member = MemberResponse(id=member_id, **data.model_dump())
    members[members.index(member)] = updated_member
    return updated_member


# A successful DELETE has no response body, so it returns HTTP 204.
@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a member",
    description="Delete a member only when no books are checked out to them.",
    responses={
        404: {"description": "Member not found"},
        409: {"description": "Member still has borrowed books"},
    },
)
def delete_member(member_id: int) -> Response:
    """Remove a member from the in-memory collection."""
    member = find_member(member_id)

    # Do not leave Books pointing at a Member who no longer exists.
    if any(book.member_id == member_id for book in books):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Delete or reassign this member's books before deleting the "
                "member"
            ),
        )

    members.remove(member)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# This nested URL reads the Books that belong to one Member.
@router.get(
    "/{member_id}/books",
    response_model=list[BookResponse],
    summary="List a member's books",
    description="Return every book currently borrowed by the requested member.",
    responses={404: {"description": "Member not found"}},
)
def list_member_books(member_id: int) -> list[BookResponse]:
    """Return every book associated with the requested member."""
    # Calling find_member first distinguishes a member with no books, which is
    # an empty list, from a member who does not exist, which is a 404.
    find_member(member_id)
    return [book for book in books if book.member_id == member_id]
