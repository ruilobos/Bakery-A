from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .models import RawMaterial, Supplier, Base_recipes, Recipe_Ingredients, Product
from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.urls import reverse
import datetime
from control.forms import Raw_Material_Form
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

# Create your views here.

class Dashboard(ListView):
    model = Product
    template_name = 'dashboard.html'
    context_object_name = 'product_list'


def rw_categories(request):
    return render(request, 'rw_categories.html')


class RawMaterialsList(ListView):
    model = RawMaterial
    template_name = 'raw_materials.html'
    context_object_name = 'rw_list'

    def get_queryset(self, **kwargs):
        try:
            queryset = RawMaterial.objects.filter(categorie__icontains=self.kwargs['pk'])
        except RawMaterial.DoesNotExist:
            queryset = None
            return queryset
    
    def get_context_data(self, **kwargs):
        context =  super(RawMaterialsList, self).get_context_data(**kwargs)
        queryset = RawMaterial.objects.filter(categorie__icontains=self.kwargs['pk'])
        queryset2 = self.kwargs['pk']
        context = {
            'categorie' : queryset2,
            'rw_list' : queryset
        }
        return context

class Raw_material_Create(CreateView):
    model = RawMaterial
    fields = '__all__'
    template_name = 'new_raw_material.html'
    success_url = reverse_lazy('control:rw_categories')
   

class Raw_material_Update(UpdateView):
    model = RawMaterial
    fields = '__all__'
    template_name = 'raw_material.html'
    success_url = reverse_lazy('control:rw_categories')
    

class Raw_material_Delete(DeleteView):
    model = RawMaterial
    template_name = 'delete_raw_material.html'
    success_url = reverse_lazy('control:rw_categories')
    



class SuppliersList(ListView):
    model = Supplier
    template_name = 'suppliers.html'


class Supplier_Create(CreateView):
    model = Supplier
    fields = '__all__'
    template_name = 'new_supplier.html'
    success_url = reverse_lazy('control:suppliers')
   

class Supplier_Update(UpdateView):
    model = Supplier
    fields = '__all__'
    template_name = 'supplier.html'
    success_url = reverse_lazy('control:suppliers')
    

class Supplier_Delete(DeleteView):
    model = Supplier
    template_name = 'delete_supplier.html'
    success_url = reverse_lazy('control:suppliers')




class Base_recipesList(ListView):
    model = Base_recipes
    template_name = 'base_recipes.html'
    context_object_name = 'base_recipes'


class Base_recipe(DetailView):
    model = Base_recipes
    template_name = 'base_recipe.html'
    context_object_name = 'base_recipe'


class Base_recipes_Create(CreateView):
    model = Base_recipes
    fields = '__all__'
    template_name = 'new_base_recipe.html'
    context_object_name = 'base_recipe'
    success_url = reverse_lazy('control:base_recipes')


class Ingredient_Create(CreateView):
    model = Recipe_Ingredients
    fields = '__all__'
    template_name = 'new_ingredient.html'
    context_object_name = 'ingredient'
    success_url = reverse_lazy('control:base_recipes')
   

class Base_recipes_Update(UpdateView):
    model = Base_recipes
    fields = '__all__'
    template_name = 'edit_base_recipe.html'
    success_url = reverse_lazy('control:base_recipes')
    

class Base_recipes_Delete(DeleteView):
    model = Base_recipes
    template_name = 'delete_base_recipe.html'
    success_url = reverse_lazy('control:base_recipes')




def products_categories(request):
    return render(request, 'products_categories.html')


class Product_List(ListView):
    model = Product
    template_name = 'products.html'
    context_object_name = 'product_list'

    def get_queryset(self, **kwargs):
        try:
            queryset = Product.objects.filter(categorie__icontains=self.kwargs['pk'])
        except Product.DoesNotExist:
            queryset = None
            return queryset
    
    def get_context_data(self, **kwargs):
        context =  super(Product_List, self).get_context_data(**kwargs)
        queryset = Product.objects.filter(categorie__icontains=self.kwargs['pk'])
        queryset2 = self.kwargs['pk']
        context = {
            'categorie' : queryset2,
            'product_list' : queryset
        }
        return context

class Product_Create(CreateView):
    model = Product
    fields = '__all__'
    template_name = 'new_product.html'
    success_url = reverse_lazy('control:products_categories')
   

class Product_Update(UpdateView):
    model = Product
    fields = '__all__'
    template_name = 'product.html'
    success_url = reverse_lazy('control:products_categories')
    

class Product_Delete(DeleteView):
    model = Product
    template_name = 'delete_product.html'
    success_url = reverse_lazy('control:products_categories')