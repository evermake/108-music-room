import base64
import datetime
from datetime import date, timedelta

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import and_, between, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.tools.utils import count_duration
from src.repositories.bookings.abc import AbstractBookingRepository
from src.schemas import (CreateBooking, ViewBooking,
                         ViewParticipantBeforeBooking)
from src.storage.sql import AbstractSQLAlchemyStorage
from src.storage.sql.models import Booking, Participant


class SqlBookingRepository(AbstractBookingRepository):
    storage: AbstractSQLAlchemyStorage

    def __init__(self, storage: AbstractSQLAlchemyStorage):
        self.storage = storage

    def _create_session(self) -> AsyncSession:
        return self.storage.create_session()

    async def create(self, booking: "CreateBooking") -> ViewBooking:
        async with self._create_session() as session:
            query = insert(Booking).values(**booking.model_dump()).returning(Booking)
            obj = await session.scalar(query)
            await session.commit()
            return ViewBooking.model_validate(obj)

    async def get_bookings_for_current_week(self, current_week: bool) -> list[ViewBooking]:
        async with (self._create_session() as session):
            next_week_delta = 0

            if not current_week:
                next_week_delta = 7
            today = date.today()
            start_of_week = (today - timedelta(days=today.weekday())) + timedelta(days=next_week_delta)
            end_of_week = start_of_week + timedelta(days=6)

            query = select(Booking).filter(between(Booking.time_start, start_of_week, end_of_week))

            objs = await session.scalars(query)
            if objs:
                return [ViewBooking.model_validate(obj) for obj in objs]

    async def delete_booking(self, booking_id) -> ViewBooking | dict[str, str]:
        async with self._create_session() as session:
            query = delete(Booking).where(Booking.id == booking_id).returning(Booking)
            obj = await session.scalar(query)
            await session.commit()
            if obj:
                return ViewBooking.model_validate(obj)
            return {"message": "No such booking"}

    async def check_collision(self, time_start: datetime.datetime, time_end: datetime.datetime) -> bool:
        async with self._create_session() as session:
            query = select(Booking).where(and_(Booking.time_start < time_end, Booking.time_end > time_start))
            collision_exists = await session.scalar(query)
            return collision_exists is not None

    async def get_participant(self, participant_id) -> ViewParticipantBeforeBooking:
        async with self._create_session() as session:
            query = select(Participant).where(Participant.id == participant_id)
            obj = await session.scalar(query)
            return ViewParticipantBeforeBooking.model_validate(obj)

    async def form_schedule(self, current_week: bool) -> str:
        xbase = 48  # origin for x
        ybase = 73  # origin for y
        xsize = 175.5  # length of the rect by x-axis
        ysize = 32  # length of the rect by x-axis

        # Create a new image using PIL
        image = Image.open("src/repositories/bookings/schedule.jpg")
        draw = ImageDraw.Draw(image)

        lightGray = (211, 211, 211)
        lightBlack = (48, 54, 59)
        red = (255, 0, 0)

        fontSimple = ImageFont.truetype("src/repositories/bookings/open_sans.ttf", size=14)

        bookings = await self.get_bookings_for_current_week(current_week)
        for booking in bookings:
            day = booking.time_start.weekday()

            ylength = await count_duration(booking.time_start, booking.time_end)
            x0 = xbase + xsize * day
            y0 = ybase + int(ysize * ((booking.time_start.hour - 7) + (booking.time_start.minute / 60.0)))
            x1 = x0 + xsize
            y1 = y0 + 31.5 * ylength

            draw.rounded_rectangle((x0, y0, x1, y1), 2, fill=lightGray)
            participant = await self.get_participant(booking.participant_id)

            alias = participant.alias
            if len(alias) > 11:
                alias = f"{alias[:11]}..."

            caption = f"{alias} "

            draw.text(
                (x0 + 2, (y0 + y1) / 2 - 9),
                text=f"{caption}{booking.time_start.strftime('%H:%M')}-{booking.time_end.strftime('%H:%M')}",
                fill=lightBlack,
                font=fontSimple,
            )

        today = datetime.date.today()
        weekday = today.weekday()

        current_datetime = datetime.datetime.now()

        current_hour = current_datetime.hour
        if 6 < current_hour < 23:
            now_x0 = xbase + xsize * weekday
            now_y0 = ybase + int(ysize * ((datetime.datetime.now().hour - 7) + (datetime.datetime.now().minute / 60)))
            draw.rounded_rectangle((now_x0, now_y0, now_x0 + xsize, now_y0 + 2), 2, fill=red)

        image.save("result.jpg")

        with open("result.jpg", "rb") as f:
            image_stream = f.read()

        image_base64 = base64.b64encode(image_stream).decode("utf-8")

        return image_base64