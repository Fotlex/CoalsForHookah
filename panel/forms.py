from django import forms

class CouponGenerationForm(forms.Form):
    quantity = forms.IntegerField(
        label="Количество купонов для генерации",
        min_value=1,
        max_value=200000, 
        initial=1000,
        help_text="Введите число от 1 до 200,000."
    )