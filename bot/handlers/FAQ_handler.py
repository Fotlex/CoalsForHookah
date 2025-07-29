from asgiref.sync import sync_to_async
from aiogram import Router, F, Bot
from aiogram.types import (InlineQuery, Message, CallbackQuery,
                           InlineQueryResultArticle, InputTextMessageContent, FSInputFile)

from bot.keyboards import *
from panel.models import FAQ



router = Router()


@router.callback_query(F.data == 'FAQ')
async def faq_helper(callback: CallbackQuery, bot: Bot):
    bot_info = await bot.get_me()
    await callback.answer(text=f'Чтобы воспользоваться'
                          f'поиском вопросов введите в любой чат @{bot_info.username}'
                          f' и выберите интересующий вас вопрос',
                          show_alert=True)


@router.inline_query()
async def faq_inline(inline_query: InlineQuery):
    try:
        questions = await sync_to_async(
            lambda: list(FAQ.objects.values_list('question', flat=True))
        )()
        
        query = inline_query.query.lower().strip()
        
        results = [
            InlineQueryResultArticle(
                id=str(i),
                title=q,
                input_message_content=InputTextMessageContent(
                    message_text=q,
                    parse_mode=None
                )
            )
            for i, q in enumerate(questions[:50]) 
            if not query or query in q.lower()
        ]
        
        await inline_query.answer(results, cache_time=60)
        
    except Exception as e:
        await inline_query.answer([], cache_time=60)
           

@router.message(F.text.in_([x.question for x in FAQ.objects.all()]))
async def on_message(message: Message):
    answer = await FAQ.objects.aget(question=message.text)
    try:
        photo = FSInputFile(answer.image.path)
        await message.answer_photo(
            photo=photo,
            caption=answer.answer
        )
    except Exception as e:
        await message.answer(text=answer.answer)
    