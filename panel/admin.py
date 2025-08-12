import random
import openpyxl
from django.contrib import admin
from panel.models import *

from django.http import HttpResponse
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import admin, messages
from django.db import transaction
from asgiref.sync import async_to_sync
from aiogram import Bot
from config import config


from .forms import CouponGenerationForm




@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name', 'last_name', 'created_at')
    fields = ('id', 'username', 'first_name', 'last_name', 'created_at')

    exclude = ('data',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class AttachmentsInline(admin.TabularInline):
    model = Attachments

    exclude = ('file_id',)

    extra = 0


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ['datetime', 'text', 'is_ok']
    readonly_fields = ['is_ok']
    inlines = [AttachmentsInline]



async def notify_winner_task(bot_token, chat_id, prize_description, raffle_name):
    bot = Bot(token=bot_token)
    try:
        text = (
            f"🎉 Поздравляем! Ваш купон оказался выигрышным! 🎉\n\n"
            f"В розыгрыше «{raffle_name}» вы выиграли:\n\n"
            f"🎁 **{prize_description}**"
        )
        await bot.send_message(chat_id, text, parse_mode="Markdown")
    finally:
        await bot.session.close()


class CouponOwnerFilter(admin.SimpleListFilter):
    title = 'статус активации' 
    parameter_name = 'owner_status' 

    def lookups(self, request, model_admin):
        return (
            ('activated', 'Активированные'),
            ('not_activated', 'Неактивированные'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'activated':
            return queryset.filter(owner__isnull=False)
        if self.value() == 'not_activated':
            return queryset.filter(owner__isnull=True)
        return queryset


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'owner', 'is_used')
    list_filter = ('is_used', CouponOwnerFilter)
    search_fields = ('code', 'owner__username')
    readonly_fields = ('code',)

    @admin.display(description='Выигранный приз')
    def get_won_prize_info(self, obj):
        if hasattr(obj, 'won_prize') and obj.won_prize:
            return f"'{obj.won_prize.description}' в '{obj.won_prize.raffle.name}'"
        return "—"

    actions = ['generate_coupons_action', 'export_unused_coupons_action']



    @admin.action(description='Сгенерировать купоны пачкой')
    def generate_coupons_action(self, request, queryset):
        if 'apply' in request.POST:
            form = CouponGenerationForm(request.POST)
            if form.is_valid():
                quantity = form.cleaned_data['quantity']

                try:
                    with transaction.atomic():
                        coupons_to_create = [
                            Coupon(owner=None, is_used=False) for _ in range(quantity)
                        ]
                        Coupon.objects.bulk_create(coupons_to_create, ignore_conflicts=True)
                    
                    self.message_user(request, f"Успешно создано {quantity} новых купонов.", messages.SUCCESS)
                    return redirect(request.get_full_path())
                
                except Exception as e:
                    self.message_user(request, f"Произошла ошибка при генерации: {e}", messages.ERROR)
                    return redirect(request.get_full_path())

        else:
            form = CouponGenerationForm()
            return render(request, 'admin/generate_coupons_intermediate.html', {
                'title': 'Генерация купонов',
                'queryset': queryset,
                'form': form
            })
        

    @admin.action(description='Выгрузить неиспользованные купоны в Excel')
    def export_unused_coupons_action(self, request, queryset):
        coupons_to_export = Coupon.objects.filter(owner__isnull=True, is_used=False).order_by('code')

        if not coupons_to_export.exists():
            self.message_user(request, "Нет неактивированных и неиспользованных купонов для выгрузки.", messages.WARNING)
            return

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = 'Неиспользованные купоны'

        worksheet.append(['Код купона'])

        for code, in coupons_to_export.values_list('code'):
            worksheet.append([code])
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename="unused_coupons.xlsx"'
        
        workbook.save(response)
        return response


class PrizeInline(admin.TabularInline):
    model = Prize
    extra = 1
    readonly_fields = ('winner_coupon',)

@admin.register(Raffle)
class RaffleAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'is_finished')
    list_filter = ('is_finished',)
    inlines = [PrizeInline]
    actions = ['run_raffle_action']
    ordering = ['-created_at']

    @admin.action(description='Провести выбранные розыгрыши')
    def run_raffle_action(self, request, queryset):
        BOT_TOKEN = config.BOT_TOKEN

        for raffle in queryset.filter(is_finished=False):
            prizes_to_award = list(raffle.prizes.all())
            available_coupons = list(Coupon.objects.filter(owner__isnull=False, is_used=False))

            
            if not prizes_to_award:
                self.message_user(request, f"Ошибка: в розыгрыше '{raffle.name}' нет призов. Розыгрыш отменен.", level=messages.ERROR)
                continue 

            if not available_coupons:
                self.message_user(request, f"Розыгрыш '{raffle.name}' завершен, но победителей не было, так как не было активированных купонов для участия.", level=messages.WARNING)
                raffle.is_finished = True 
                raffle.save()
                continue
            
            coupon_ids_to_deactivate = [coupon.code for coupon in available_coupons]
            
            random.shuffle(prizes_to_award)
            random.shuffle(available_coupons)

            actual_winners_count = min(len(prizes_to_award), len(available_coupons))

            for i in range(actual_winners_count):
                winning_coupon = available_coupons[i]
                awarded_prize = prizes_to_award[i]

                awarded_prize.winner_coupon = winning_coupon
                awarded_prize.save()
                
                winning_coupon.is_used = True
                winning_coupon.save()
                
                async_to_sync(notify_winner_task)(
                    bot_token=BOT_TOKEN, 
                    chat_id=winning_coupon.owner.id,
                    prize_description=awarded_prize.description, 
                    raffle_name=raffle.name
                )
                
            if coupon_ids_to_deactivate: 
                Coupon.objects.filter(code__in=coupon_ids_to_deactivate).update(is_used=True)

            
            raffle.is_finished = True
            raffle.save()
            
            self.message_user(request, f"Розыгрыш '{raffle.name}' успешно проведен! Награждено победителей: {actual_winners_count}.")


admin.site.register(FAQ)
