from aiogram import F, Router, Bot
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    FSInputFile
)
from aiogram.filters.callback_data import CallbackData
from asgiref.sync import sync_to_async
from django.db import models 

from panel.models import FAQ

from bot.keyboards import *
from panel.models import FAQ
from django.db import models


router = Router()


class PaginationCallback(CallbackData, prefix="faq_page"):
    action: str  
    page: int    

class FaqQuestionCallback(CallbackData, prefix="faq_q"):
    question_id: int 


ITEMS_PER_PAGE = 5  


async def get_faq_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    all_questions_queryset = await sync_to_async(FAQ.objects.order_by)('id')
    all_questions_list = await sync_to_async(list)(all_questions_queryset)

    total_questions = len(all_questions_list)

    total_pages = (total_questions + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

   
    start_index = page * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE

    current_page_questions = all_questions_list[start_index:end_index]

    buttons = []
    
    for faq_item in current_page_questions:
        buttons.append([
            InlineKeyboardButton(
                text=faq_item.question,
                callback_data=FaqQuestionCallback(question_id=faq_item.id).pack()
            )
        ])

    pagination_buttons = []
    if page > 0: 
        pagination_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=PaginationCallback(action="prev", page=page - 1).pack()
            )
        )
    if page < total_pages - 1: 
        pagination_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=PaginationCallback(action="next", page=page + 1).pack()
            )
        )
    
    
    if pagination_buttons:
        buttons.append(pagination_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == 'FAQ')
async def faq_helper(message: Message):
    keyboard = await get_faq_keyboard(page=0)
    await message.answer(
        text="Выберите вопрос из списка FAQ:",
        reply_markup=keyboard
    )


@router.callback_query(PaginationCallback.filter())
async def paginate_faq_questions(callback: CallbackQuery, callback_data: PaginationCallback):
    new_page = callback_data.page
    keyboard = await get_faq_keyboard(page=new_page)
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer() 

@router.callback_query(FaqQuestionCallback.filter())
async def send_faq_answer(callback: CallbackQuery, callback_data: FaqQuestionCallback):
    try:
        faq_item = await sync_to_async(FAQ.objects.aget)(id=callback_data.question_id)

        try:
            photo = FSInputFile(faq_item.image.path)
            await callback.message.answer_photo(
                photo=photo,
                caption=faq_item.answer
            )
        except Exception as e:
            await callback.message.answer(text=faq_item.answer)
            

        await callback.answer() 

    except models.ObjectDoesNotExist: 
        await callback.message.answer("Извините, этот вопрос FAQ не найден. Возможно, он был удален.")
    except Exception as e:
        await callback.message.answer("Произошла ошибка при получении ответа. Пожалуйста, попробуйте позже.")
        print(e)
    