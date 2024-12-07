from django import forms
from .models import *
from django_countries.fields import CountryField


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'desc': forms.Textarea(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'product_available_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'img': forms.FileInput(attrs={'class': 'form-control'}),
        }


class CheckoutForm(forms.Form):
    # Street Address Field
    street_address = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': '1234 Main St'
            }
        )
    )

    # Apartment Address Field
    apartment_address = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Apartment or suite'
            }
        )
    )

    # Country Field
    country = CountryField(
        blank_label='(select country)'
    ).formfield(
        widget=forms.Select(
            attrs={
                'class': 'custom-select d-block w-100'
            }
        )
    )

    # ZIP Field
    zip = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control'
            }
        )
    )
