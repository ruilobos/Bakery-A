from django.forms import ModelForm
from .models import RawMaterial

class Raw_Material_Form(ModelForm):
    class Meta:
        model = RawMaterial
        fields = '__all__'