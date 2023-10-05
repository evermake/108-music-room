import datetime
from abc import ABCMeta, abstractmethod

from schemas import (CreateParticipant, ViewBooking,
                     ViewParticipantBeforeBooking)


class AbstractParticipantRepository(metaclass=ABCMeta):
    @abstractmethod
    async def create(self, participant: "CreateParticipant") -> "ViewParticipantBeforeBooking":
        ...

    @abstractmethod
    async def change_status(
        self, participant_id: "ViewParticipantBeforeBooking", new_status: str
    ) -> "ViewParticipantBeforeBooking":
        ...

    @abstractmethod
    async def get_participant_bookings(self, participant_id: int) -> list["ViewBooking"]:
        ...

    @abstractmethod
    async def get_status(self, participant_id: int) -> str:
        ...

    @abstractmethod
    async def remaining_weekly_hours(self, participant_id: int) -> float:
        ...

    @abstractmethod
    async def remaining_daily_hours(self, participant_id: int, date: datetime.datetime) -> float:
        ...
