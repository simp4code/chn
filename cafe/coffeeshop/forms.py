# forms.py
from django import forms
from .models import Product

class FileForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['img', 'name', 'price', 'quantity']
        widgets = {
            'img': forms.ClearableFileInput(attrs={'class': 'custom-file-input'}),
            'name': forms.TextInput(attrs={'class': 'custom-text-input'}),
            'price': forms.TextInput(attrs={'class': 'custom-text-input'}),
            'quantity': forms.TextInput(attrs={'class': 'custom-text-input'}),
        }
class VerificationForm(forms.Form):
    verification_code = forms.CharField(max_length=50)