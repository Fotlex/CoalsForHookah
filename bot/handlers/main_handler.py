import os

from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from django.conf import settings
from bot.keyboards import *
from panel.models import User

router = Router()

class StateCode(StatesGroup):
    wait_code = State()

@router.message(CommandStart())
async def start_f(message: Message):
    await message.answer('Приветственное сообщение', reply_markup=main_keyboard)


@router.message(F.text == 'Добавить купон')
async def add_coupon_f(message: Message, state: FSMContext):
    photo_path = os.path.join(settings.MEDIA_ROOT, 'example', 'example_photo.jpg')
    photo_file = FSInputFile(photo_path)

    try:
        await message.answer_photo(
            photo=photo_file,
            caption='Укажите код на вашей упаковке углей, на фото выше пример кода'
        )
    except Exception as e:
        await message.answer(
            text='Укажите код на вашей упаковке углей: '
        )

    await state.set_state(StateCode.wait_code)


