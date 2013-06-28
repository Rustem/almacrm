from Product.models import Product
from Django import forms
from django.forms.widgets import Textarea

class ProductForm(forms.ModelForm):
	name=models.CharField(required=True)
	price=models.DecimalField(default=0)
	quantity=models.IntegerField(default=0)
	description=models.CharField(widget=forms.Textarea)