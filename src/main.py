from fastapi import FastAPI

from src.api import docs
from src.api.dependencies import Dependencies
from src.api.docs import generate_unique_operation_id
from src.api.routers import routers
from src.config import settings
from src.repositories.auth.abc import AbstractAuthRepository
from src.repositories.auth.repository import SqlAuthRepository
from src.repositories.bookings.abc import AbstractBookingRepository
from src.repositories.bookings.repository import SqlBookingRepository
from src.repositories.participants.abc import AbstractParticipantRepository
from src.repositories.participants.repository import SqlParticipantRepository
from src.storage.sql import SQLAlchemyStorage, AbstractSQLAlchemyStorage

# App definition
app = FastAPI(
    title=docs.TITLE,
    summary=docs.SUMMARY,
    description=docs.DESCRIPTION,
    version=docs.VERSION,
    contact=docs.CONTACT_INFO,
    license_info=docs.LICENSE_INFO,
    openapi_tags=docs.TAGS_INFO,
    servers=[
        {"url": settings.APP_ROOT_PATH, "description": "Current"},
    ],
    root_path=settings.APP_ROOT_PATH,
    root_path_in_servers=False,
    swagger_ui_oauth2_redirect_url=None,
    generate_unique_id_function=generate_unique_operation_id,
)


async def setup_repositories():
    # ------------------- Repositories Dependencies -------------------
    storage = SQLAlchemyStorage.from_url(settings.DB_URL)
    participant_repository = SqlParticipantRepository(storage)
    booking_repository = SqlBookingRepository(storage)
    auth_repository = SqlAuthRepository(storage)
    Dependencies.register_provider(AbstractSQLAlchemyStorage, storage)
    Dependencies.register_provider(AbstractParticipantRepository, participant_repository)
    Dependencies.register_provider(AbstractBookingRepository, booking_repository)
    Dependencies.register_provider(AbstractAuthRepository, auth_repository)

    # await storage.drop_all()
    # await storage.create_all()


@app.on_event("startup")
async def startup_event():
    await setup_repositories()


for router in routers:
    app.include_router(router)
