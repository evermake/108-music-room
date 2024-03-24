from aiogram import Router, Bot
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.state import any_state
from aiogram.types import Message

from src.bot.constants import rules_confirmation_message, instructions_url, how_to_get_url, tg_chat_url
from src.bot.filters import RegisteredUserFilter
from src.bot.menu import menu_kb

router = Router(name="registration")


class RegistrationStates(StatesGroup):
    rules_confirmation_requested = State()


@router.message(any_state, ~RegisteredUserFilter())
@router.callback_query(any_state, ~RegisteredUserFilter())
async def not_registered(user: types.User, bot: Bot, state: FSMContext):
    from src.bot.api import api_client

    success, detail = await api_client.start_registration(user.id)

    if success is None:
        await bot.send_message(
            user.id, "Welcome! To continue, you need to connect your Telegram account to the InnoHassle account."
        )
    elif success is False:
        from src.bot.menu import menu_kb

        await bot.send_message(user.id, "Welcome! Choose the action you're interested in.", reply_markup=menu_kb)
    elif success is True:
        from src.bot.constants import rules_confirmation_message, rules_message

        confirm_kb = types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(
                        text=rules_confirmation_message,
                    )
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await state.set_state(RegistrationStates.rules_confirmation_requested)
        await bot.send_message(user.id, rules_message, reply_markup=confirm_kb)


@router.message(RegistrationStates.rules_confirmation_requested)
async def confirm_rules(message: Message, state: FSMContext):
    if message.text[:100] == rules_confirmation_message.format(name=(await state.get_data()))[:100]:
        text = (
            "You have successfully registered.\n\n"
            "❗️ Access to the Sports Complex will appear after submitting the list of users (usually on "
            "Monday)."
        )

        await message.answer(text, reply_markup=menu_kb, parse_mode="HTML")

        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="Instructions", url=instructions_url),
                    types.InlineKeyboardButton(text="Location", url=how_to_get_url),
                    types.InlineKeyboardButton(text="Telegram chat", url=tg_chat_url),
                ]
            ]
        )

        await message.answer(
            "If you have any questions, you can ask them in the chat or read the instructions.",
            reply_markup=keyboard,
        )

        await state.clear()
    else:
        await message.answer("You haven't confirmed the rules. Please, try again.")
