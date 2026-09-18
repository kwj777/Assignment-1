"""Temporary in-memory storage shared by the API routers."""

from app.schemas.books import BookResponse
from app.schemas.members import MemberResponse

# These lists reset whenever the application restarts. A database and repository
# layer will replace them in Assignment 2.
members: list[MemberResponse] = [
    MemberResponse(
        id=1,
        name="Ada Lovelace",
        email="ada.lovelace@example.com",
        membership_id="LIB-000001",
        phone="555-010-1234",
    )
]

books: list[BookResponse] = [
    BookResponse(
        id=1,
        title="The Pragmatic Programmer",
        author="Andrew Hunt",
        isbn="978-0-201-61622-4",
        published_year=1999,
        member_id=1,
    )
]
