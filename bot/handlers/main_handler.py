import os

from asgiref.sync import sync_to_async

from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.utils.markdown import hbold, hcode
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from django.conf import settings
from bot.keyboards import *
from panel.models import User, Coupon, Raffle

router = Router()


class StateCode(StatesGroup):
    wait_code = State()


MAIN_TEXT = '''Добро пожаловать в бот для проведения розыгрышей BauBau_bot!

В этом боте вы можете зарегистрировать свой код с пачки угля BauBau и поучаствовать в ежемесячном розыгрыше призов. 

➡️ Призовой фонд обновляется каждый месяц
➡️ Победители выбираются случайным образом
➡️ Каждый участник может регистрировать неограниченное количество купонов. Больше угля — больше шансов на победу!
➡️ Итоги подводятся каждый последний день месяца

❗️Чтобы выиграть один из призов, просто нажмите кнопку «добавить купон» и укажите ваш уникальный код.'''


@sync_to_async
def get_latest_active_raffle_with_prizes():
    try:
        raffle = Raffle.objects.filter(is_finished=False).latest('created_at')
        
        prizes = raffle.prizes.all() 

        return raffle, list(prizes) 
    except Exception as e:
        print(f"Ошибка при получении розыгрыша: {e}") 
        return None, None



@router.message(CommandStart())
async def start_f(message: Message):
    await message.answer(text=MAIN_TEXT, reply_markup=main_keyboard)


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


@router.message(F.text, StateCode.wait_code)
async def test_code_f(message: Message, state: FSMContext, user: User):
    code = message.text
    await state.clear()

    try:
        coupon = await Coupon.objects.select_related('owner').aget(code=code)

        if coupon.owner is None:
            coupon.owner = user
            await coupon.asave()

            await message.answer('Поздравляем, вам добавлен 1 купон', reply_markup=main_keyboard)
            return
        
        await message.answer('К сожалению, этот код уже был указан', reply_markup=main_keyboard)

    except Coupon.DoesNotExist:
        await message.answer('К сожалению вы указали несуществующий код', reply_markup=main_keyboard)


@router.message(F.text == 'Информация о розыгрыше')
async def info_f(message: Message):
    raffle, prizes = await get_latest_active_raffle_with_prizes() 

    if raffle and prizes: 
        prizes_text = "\n".join([f"  - {p.description}" for p in prizes])
        
        response_text = (
            f" **Активный розыгрыш:** {raffle.name} \n\n"
            f"*{raffle.description}*\n\n"
            f"🎁 **Призы:**\n"
            f"{prizes_text}"
        )
        await message.answer(response_text, parse_mode="Markdown")
        
    elif raffle and not prizes: 
        response_text = (
            f" **Активный розыгрыш:** {raffle.name} \n\n"
            f"*{raffle.description}*\n\n"
            f"В этом розыгрыше пока нет призов. Следите за обновлениями!"
        )
        await message.answer(response_text, parse_mode="Markdown")

    else: 
        await message.answer("В данный момент нет активных розыгрышей.")


@router.message(F.text == 'Мои купоны')
async def my_f(message: Message, user: User):
    try:
        active_coupons = await sync_to_async(list)(
            Coupon.objects.filter(owner=user, is_used=False)
        )
        
        if not active_coupons:
            await message.answer("У тебя пока нет активных купонов.")
            return

        total_coupons_count = len(active_coupons)
        
        header = f"👋 <b>{user.first_name}</b>!\nКоличество твоих купонов: <b>{total_coupons_count}</b>\n\n"
        
        coupon_list_items = ""
        for coupon in active_coupons:
            coupon_list_items += f"🔸 <code>{coupon.code}</code>\n"

        response_text = header + coupon_list_items
        
        await message.answer(response_text, parse_mode="HTML")

    except Exception as e:
        print(f"Ошибка при обработке купонов для пользователя {user.id}: {e}")
        await message.answer("Произошла внутренняя ошибка при получении ваших купонов. Попробуйте позже.")











