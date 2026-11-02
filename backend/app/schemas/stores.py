from pydantic import BaseModel, Field


class CreateStoreRequest(BaseModel):
    name: str = Field(min_length=1)


class CreateStoreResponse(BaseModel):
    id: int
    name: str
    role: str


class StoreItem(BaseModel):
    id: int
    name: str
    role: str


class StoreListResponse(BaseModel):
    items: list[StoreItem]
    total: int
    page: int
    page_size: int


class CreateInvitationRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    store: str = Field(min_length=1)


class CreateInvitationResponse(BaseModel):
    email: str
    store: str


class InvitationItem(BaseModel):
    email: str
    store: str


class InvitationListResponse(BaseModel):
    items: list[InvitationItem]
    total: int
    page: int
    page_size: int


class AcceptInvitationRequest(BaseModel):
    store: str = Field(min_length=1)


class AcceptInvitationResponse(BaseModel):
    store: str
    role: str
