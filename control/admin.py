from django.contrib import admin
from .models import RawMaterial, Supplier, Base_recipes, Recipe_Ingredients, Product, Bs_Ingredients

# Register your models here.
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = ('description', 'supplier', 'categorie', 'price', 'quantity', 'unit')
    list_filter = ('description', 'supplier', 'categorie')
    search_fields = ['description']

admin.site.register(RawMaterial, RawMaterialAdmin)


class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(Supplier, SupplierAdmin)


# Register your models here.
class Base_Recipe_Admin(admin.ModelAdmin):
    list_display = ('name', 'recipe_yeld', 'yield_unit')
    list_filter = ['name']
    search_fields = ['name']

admin.site.register(Base_recipes, Base_Recipe_Admin)


class Bs_IngredientsAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'base_recipe', 'quantity', 'unit')
    list_filter = ['ingredient']

admin.site.register(Bs_Ingredients,Bs_IngredientsAdmin)


class Recipe_IngredientsAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'product', 'quantity', 'unit')
    list_filter = ['ingredient']

admin.site.register(Recipe_Ingredients, Recipe_IngredientsAdmin)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'recipe_yeld', 'yield_unit', 'price', 'vat')
    search_fields = ['name']

admin.site.register(Product, ProductAdmin)