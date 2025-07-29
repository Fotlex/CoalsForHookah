import uuid

from django.db import models


def generate_short_uuid():
    return uuid.uuid4().hex[:6].upper()

class User(models.Model):
    id = models.BigIntegerField('Идентификатор Телеграм', primary_key=True, blank=False)

    username = models.CharField('Юзернейм', max_length=64, null=True, blank=True)
    first_name = models.CharField('Имя', null=True, blank=True)
    last_name = models.CharField('Фамилия', null=True, blank=True)

    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True, blank=True)

    data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f'id{self.id} | @{self.username or "-"} {self.first_name or "-"} {self.last_name or "-"}'

    class Meta:
        verbose_name = 'Телеграм пользователь'
        verbose_name_plural = 'Телеграм пользователи'


class Coupon(models.Model):
    code = models.CharField(
        primary_key=True,           
        max_length=6,               
        default=generate_short_uuid,   
        editable=False,       
        verbose_name="Код купона"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coupons',
        verbose_name="Владелец"
    )
    is_used = models.BooleanField(default=False, verbose_name="Использован (выиграл)")


    def __str__(self):
        owner_info = f"(владелец: {self.owner.first_name})" if self.owner else "(не активирован)"
        return f"Купон {self.code} {owner_info}"

    class Meta:
        verbose_name = "Купон"
        verbose_name_plural = "Купоны"


class Raffle(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название розыгрыша")
    description = models.TextField(verbose_name="Описание")
    is_finished = models.BooleanField(default=False, verbose_name="Завершен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")


    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name, verbose_name_plural = "Розыгрыш", "Розыгрыши"
        ordering = ['-created_at']


class Prize(models.Model):
    raffle = models.ForeignKey(Raffle, on_delete=models.CASCADE, related_name='prizes', verbose_name="Розыгрыш")
    description = models.CharField(max_length=255, verbose_name="Описание приза")
    winner_coupon = models.OneToOneField(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_prize',
        verbose_name="Выигравший купон"
    )
    def __str__(self): return self.description
    class Meta: verbose_name, verbose_name_plural = "Приз", "Призы"



class Attachments(models.Model):
    types = {
        'photo': 'Фото',
        'video': 'Видео',
        'document': 'Документ'
    }

    type = models.CharField('Тип вложения', choices=types)
    file = models.FileField('Файл', upload_to='media/mailing')
    file_id = models.TextField(null=True)
    mailing = models.ForeignKey('Mailing', on_delete=models.SET_NULL, null=True, related_name='attachments')

    class Meta:
        verbose_name = 'Вложение'
        verbose_name_plural = 'Вложения'


class Mailing(models.Model):
    text = models.TextField('Текст', blank=True, null=True)
    datetime = models.DateTimeField('Дата/Время')
    is_ok = models.BooleanField('Статус отправки', default=False)

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
