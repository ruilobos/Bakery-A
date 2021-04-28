from django.forms import ModelForm
from .models import RawMaterial, Recipe_Ingredients

class Raw_Material_Form(ModelForm):
    class Meta:
        model = RawMaterial
        fields = '__all__'
