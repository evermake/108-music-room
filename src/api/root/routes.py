import datetime
from zlib import crc32

import icalendar
from fastapi import Response

from src.api.dependencies import Dependencies
from src.api.root import router
from src.repositories.bookings.abc import AbstractBookingRepository


def _calendar_baseline():
    main_calendar = icalendar.Calendar(
        prodid="-//one-zero-eight//InNoHassle Schedule",
        version="2.0",
        method="PUBLISH",
    )
    main_calendar["x-wr-calname"] = "Music Room schedule from innohassle.ru"
    main_calendar["x-wr-timezone"] = "Europe/Moscow"
    main_calendar["x-wr-caldesc"] = "Generated by InNoHassle Schedule"
    return main_calendar


def _booking_to_vevent(booking):
    string_to_hash = str(booking.id)
    hash_ = crc32(string_to_hash.encode("utf-8"))
    uid = "music-room-%x@innohassle.ru" % abs(hash_)

    vevent = icalendar.Event()
    vevent.add("uid", uid)
    vevent.add("dtstart", icalendar.vDatetime(booking.time_start))
    vevent.add("dtend", icalendar.vDatetime(booking.time_end))
    vevent.add("location", "Music Room 020")
    vevent.add("summary", f"booking @{booking.participant_alias}")
    return vevent


@router.get(
    "/music-room.ics",
    responses={
        200: {
            "description": "ICS file with schedule of the music room",
            "content": {"text/calendar": {"schema": {"type": "string", "format": "binary"}}},
        },
    },
    response_class=Response,
    tags=["ICS"],
)
async def get_music_room_ics():
    main_calendar = _calendar_baseline()

    booking_repository = Dependencies.get(AbstractBookingRepository)
    from_date = datetime.date.today() - datetime.timedelta(days=14)
    to_date = datetime.date.today() + datetime.timedelta(days=14)
    bookings = await booking_repository.get_bookings(from_date, to_date)
    dtstamp = icalendar.vDatetime(datetime.datetime.now())
    for booking in bookings:
        vevent = _booking_to_vevent(booking)
        vevent.add("dtstamp", dtstamp)
        main_calendar.add_component(vevent)

    ical_bytes = main_calendar.to_ical()

    return Response(content=ical_bytes, media_type="text/calendar")


@router.get(
    "/participants/{participant_id}/bookings.ics",
    responses={
        200: {
            "description": "ICS file with schedule of the participant",
            "content": {"text/calendar": {"schema": {"type": "string", "format": "binary"}}},
        },
    },
    response_class=Response,
    tags=["Participants", "ICS"],
)
async def get_participant_ics(participant_id: int):
    main_calendar = _calendar_baseline()
    booking_repository = Dependencies.get(AbstractBookingRepository)
    bookings = await booking_repository.get_participant_bookings(participant_id)
    dtstamp = icalendar.vDatetime(datetime.datetime.now())
    for booking in bookings:
        vevent = _booking_to_vevent(booking)
        vevent.add("dtstamp", dtstamp)
        main_calendar.add_component(vevent)

    ical_bytes = main_calendar.to_ical()
    return Response(content=ical_bytes, media_type="text/calendar")
