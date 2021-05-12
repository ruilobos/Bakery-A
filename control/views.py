from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .models import RawMaterial, Supplier, Base_recipes, Recipe_Ingredients, Product, Bs_Ingredients
from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.urls import reverse
import datetime
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
import csv
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.template.defaulttags import register


#-------------------------------------------------#
# Generic Functions
#-------------------------------------------------#

# Retun as a dictionary iten
...
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


#-------------------------------------------------#
#Dashboard Views
#-------------------------------------------------#

# List all products
class Dashboard(ListView):
    model = Recipe_Ingredients
    template_name = 'dashboard.html'
    context_object_name = 'product_list'

    def get_queryset(self, **kwargs):
        try:
            queryset = Recipe_Ingredients.objects.all()
        except Recipe_Ingredients.DoesNotExist:
            queryset = None
            return queryset
    
    def get_context_data(self, **kwargs):
        context =  super(Dashboard, self).get_context_data(**kwargs)
        queryset = Recipe_Ingredients.objects.all()
        queryset2 = Product.objects.all()
        
        # Calculate Unit Cost
        price_list = []
        unit_cost = {}
        for iten in Recipe_Ingredients.objects.all():
            description = iten.product.name
            if description not in price_list:
                price_list.append(description)

        for product in price_list:
            cost = 0
            for ingredient in Recipe_Ingredients.objects.filter(product__name__icontains=product):
                cost += ((float(ingredient.ingredient.price) * (float(ingredient.quantity))) / float(ingredient.product.recipe_yeld))
            unit_cost[product] = "{:.2f}".format(float(cost))

        # Calculate Net Price
        price_list = []
        net_value = {}
        for iten in Recipe_Ingredients.objects.all():
            description = iten.product.name
            if description not in price_list:
                price_list.append(description)

        for product in price_list:
            cost = 0
            for ingredient in Recipe_Ingredients.objects.filter(product__name__icontains=product):
                cost = (float(ingredient.product.price)*(1-(float(ingredient.product.vat))))
            net_value[product] = "{:.2f}".format(float(cost))

        # Calculate Margin percent
        price_list = []
        margin_percent = {}
        for iten in Recipe_Ingredients.objects.all():
            description = iten.product.name
            if description not in price_list:
                price_list.append(description)

        for product in price_list:
            cost = 0
            for ingredient in Recipe_Ingredients.objects.filter(product__name__icontains=product):
                net_price = (float(ingredient.product.price)*(1-(float(ingredient.product.vat))))
                cost += ((float(ingredient.ingredient.price) * (float(ingredient.quantity))) / float(ingredient.product.recipe_yeld))
            margin = (net_price - cost)
            margin_percent[product] = "{:.2f}".format((margin/net_price)*100)
        
        context = {
            'ingre_list' : queryset,
            'product_list' : queryset2,
            'unit_cost' : unit_cost,
            'margin_percent' : margin_percent,
            'net_value' : net_value,
        }
        return context


#-------------------------------------------------#
#Raw Materials Views
#-------------------------------------------------#

# Render Raw Material Categories Page
def rw_categories(request):
    return render(request, 'rw_categories.html')


# List all Raw Materials in each categorie
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


# Create a new Raw Material
class Raw_material_Create(CreateView):
    model = RawMaterial
    fields = '__all__'
    template_name = 'new_raw_material.html'
    success_url = reverse_lazy('control:rw_categories')
   

# Update a Raw Material
class Raw_material_Update(UpdateView):
    model = RawMaterial
    fields = '__all__'
    template_name = 'raw_material.html'
    success_url = reverse_lazy('control:rw_categories')
    

# Delete a Raw Material
class Raw_material_Delete(DeleteView):
    model = RawMaterial
    template_name = 'delete_raw_material.html'
    success_url = reverse_lazy('control:rw_categories')
    

#-------------------------------------------------#
#Suppliers Views
#-------------------------------------------------#

# List all Suppliers
class SuppliersList(ListView):
    model = Supplier
    template_name = 'suppliers.html'


# Create a new Supplier
class Supplier_Create(CreateView):
    model = Supplier
    fields = '__all__'
    template_name = 'new_supplier.html'
    success_url = reverse_lazy('control:suppliers')
   

# Update a Supplier
class Supplier_Update(UpdateView):
    model = Supplier
    fields = '__all__'
    template_name = 'supplier.html'
    success_url = reverse_lazy('control:suppliers')
    

# Delete a Supplier
class Supplier_Delete(DeleteView):
    model = Supplier
    template_name = 'delete_supplier.html'
    success_url = reverse_lazy('control:suppliers')


#-------------------------------------------------#
#Base Recipes Views
#-------------------------------------------------#.

# List all Base Recipes (Inicial Page)
class Base_recipesList(ListView):
    model = Base_recipes
    template_name = 'base_recipes.html'
    context_object_name = 'base_recipes'


# Show Base Recipe Details Page
class Base_recipe(ListView):
    model = Bs_Ingredients
    template_name = 'base_recipe.html'
    context_object_name = 'base_recipe'

    def get_queryset(self, **kwargs):
        try:
            queryset = Bs_Ingredients.objects.filter(id__icontains=self.kwargs['pk'])
        except Base_recipes.DoesNotExist:
            queryset = None
            return queryset
    
    def get_context_data(self, **kwargs):
        context =  super(Base_recipe, self).get_context_data(**kwargs)
        queryset = Bs_Ingredients.objects.filter(base_recipe__id__icontains=self.kwargs['pk'])
        queryset2 = Base_recipes.objects.get(id__icontains=self.kwargs['pk'])
        
        # Calculate Recipe Cost
        price_list = []
        recipe_cost = {}
        for iten in Bs_Ingredients.objects.all():
            description = iten.base_recipe.name
            if description not in price_list:
                price_list.append(description)

        for product in price_list:
            cost = 0
            for ingredient in Bs_Ingredients.objects.filter(base_recipe__name__icontains=product):
                cost += (float(ingredient.ingredient.price) * (float(ingredient.quantity)))
            recipe_cost[product] = "{:.2f}".format(float(cost))

        # Calculate Unit Cost
        price_list = []
        unit_cost = {}
        for iten in Bs_Ingredients.objects.all():
            description = iten.base_recipe.name
            if description not in price_list:
                price_list.append(description)

        for product in price_list:
            cost = 0
            for ingredient in Bs_Ingredients.objects.filter(base_recipe__name__icontains=product):
                cost += ((float(ingredient.ingredient.price) * (float(ingredient.quantity))) / float(ingredient.base_recipe.recipe_yeld))
            unit_cost[product] = "{:.2f}".format(float(cost))


        context = {
            'ingre_list' : queryset,
            'br_list' : queryset2,
            'recipe_cost' : recipe_cost,
            'unit_cost' : unit_cost,
        }
        return context


# Create a new Base Recipe
class Base_recipes_Create(CreateView):
    model = Base_recipes
    fields = '__all__'
    template_name = 'new_base_recipe.html'
    context_object_name = 'base_recipe'
    success_url = reverse_lazy('control:base_recipes')


# Update a Base Recipe
class Base_recipes_Update(UpdateView):
    model = Base_recipes
    fields = '__all__'
    template_name = 'edit_base_recipe.html'
        

# Delete a Base Recipe
class Base_recipes_Delete(DeleteView):
    model = Base_recipes
    template_name = 'delete_base_recipe.html'
    success_url = reverse_lazy('control:base_recipes')


# Add ingredient to the Base Recipe
class Br_Ingre_Create(CreateView):
    model = Bs_Ingredients
    fields = ['ingredient', 'quantity', 'unit']
    template_name = 'new_ingredient.html'

    def form_valid(self, form):
        form.instance.base_recipe_id = self.kwargs['pk']
        return super(Br_Ingre_Create, self).form_valid(form)


# Update ingredient in Base Recipe
class Br_Ingre_Update(UpdateView):
    model = Bs_Ingredients
    fields = ['ingredient', 'quantity', 'unit']
    template_name = 'ingredient.html'
    

# Delete ingredient in Base Recipe
class Br_Ingre_Delete(DeleteView):
    model = Bs_Ingredients
    template_name = 'delete_ingredient.html'
   


#-------------------------------------------------#
#Products Views
#-------------------------------------------------#

# List products categorie
def products_categories(request):
    return render(request, 'products_categories.html')


# Create a new product
class Pro_Ingre_Create(CreateView):
    model = Recipe_Ingredients
    fields = ['ingredient', 'quantity', 'unit']
    template_name = 'new_ingredient.html'

    def form_valid(self, form):
        form.instance.product_id = self.kwargs['pk']
        return super(Pro_Ingre_Create, self).form_valid(form)
   

# Update a Product
class Pro_Ingre_Update(UpdateView):
    model = Recipe_Ingredients
    fields = ['ingredient', 'quantity', 'unit']
    template_name = 'ingredient.html'


# Delete a Product
class Pro_Ingre_Delete(DeleteView):
    model = Recipe_Ingredients
    template_name = 'delete_ingredient.html'
    success_url = reverse_lazy('control:products_categories')


# List all Products in each categorie
class Product_List(ListView):
    model = Recipe_Ingredients
    template_name = 'products.html'
    context_object_name = 'product_list'

    def get_queryset(self, **kwargs):
        try:
            queryset = Recipe_Ingredients.objects.filter(product__categorie__icontains=self.kwargs['pk'])
        except Recipe_Ingredients.DoesNotExist:
            queryset = None
            return queryset
    
    def get_context_data(self, **kwargs):
        context =  super(Product_List, self).get_context_data(**kwargs)
        queryset = Recipe_Ingredients.objects.filter(product__categorie__icontains=self.kwargs['pk'])
        queryset2 = self.kwargs['pk']
        queryset3 = Product.objects.filter(categorie__icontains=self.kwargs['pk'])
        
        # Calculate Recipe Cost
        price_list = []
        recipe_cost = {}
        for iten in Recipe_Ingredients.objects.all():
            description = iten.product.name
            if description not in price_list:
                price_list.append(description)

        for product in price_list:
            cost = 0
            for ingredient in Recipe_Ingredients.objects.filter(product__name__icontains=product):
                cost += (float(ingredient.ingredient.price) * (float(ingredient.quantity)))
            recipe_cost[product] = "{:.2f}".format(float(cost))

        # Calculate Unit Cost
        price_list = []
        unit_cost = {}
        for iten in Recipe_Ingredients.objects.all():
            description = iten.product.name
            if description not in price_list:
                price_list.append(description)

        for product in price_list:
            cost = 0
            for ingredient in Recipe_Ingredients.objects.filter(product__name__icontains=product):
                cost += ((float(ingredient.ingredient.price) * (float(ingredient.quantity))) / float(ingredient.product.recipe_yeld))
            unit_cost[product] = "{:.2f}".format(float(cost))

        # Calculate Net Price
        price_list = []
        net_value = {}
        for iten in Recipe_Ingredients.objects.all():
            description = iten.product.name
            if description not in price_list:
                price_list.append(description)

        for product in price_list:
            cost = 0
            for ingredient in Recipe_Ingredients.objects.filter(product__name__icontains=product):
                cost = (float(ingredient.product.price)*(1-(float(ingredient.product.vat))))
            net_value[product] = "{:.2f}".format(float(cost))
        
        # Calculate Margin value
        price_list = []
        margin_value = {}
        for iten in Recipe_Ingredients.objects.all():
            description = iten.product.name
            if description not in price_list:
                price_list.append(description)

        for product in price_list:
            cost = 0
            for ingredient in Recipe_Ingredients.objects.filter(product__name__icontains=product):
                net_price = (float(ingredient.product.price)*(1-(float(ingredient.product.vat))))
                cost += ((float(ingredient.ingredient.price) * (float(ingredient.quantity))) / float(ingredient.product.recipe_yeld))
            margin_value[product] = "{:.2f}".format((net_price - cost))

        # Calculate Margin percent
        price_list = []
        margin_percent = {}
        for iten in Recipe_Ingredients.objects.all():
            description = iten.product.name
            if description not in price_list:
                price_list.append(description)

        for product in price_list:
            cost = 0
            for ingredient in Recipe_Ingredients.objects.filter(product__name__icontains=product):
                net_price = (float(ingredient.product.price)*(1-(float(ingredient.product.vat))))
                cost += ((float(ingredient.ingredient.price) * (float(ingredient.quantity))) / float(ingredient.product.recipe_yeld))
            margin = (net_price - cost)
            margin_percent[product] = "{:.2f}".format((margin/net_price)*100)
        
        context = {
            'categorie' : queryset2,
            'ingre_list' : queryset,
            'product_list' : queryset3,
            'recipe_cost' : recipe_cost,
            'unit_cost' : unit_cost,
            'margin_value' : margin_value,
            'margin_percent' : margin_percent,
            'net_value' : net_value,
        }
        return context


# Add new ingredient to the product
class Product_Create(CreateView):
    model = Product
    fields = '__all__'
    template_name = 'new_product.html'
    success_url = reverse_lazy('control:products_categories')
   

# Update a ingredient in product
class Product_Update(UpdateView):
    model = Product
    fields = '__all__'
    template_name = 'product.html'
    success_url = reverse_lazy('control:products_categories')
    

# Delete a ingredient in Product
class Product_Delete(DeleteView):
    model = Product
    template_name = 'delete_product.html'
    success_url = reverse_lazy('control:products_categories')


#-------------------------------------------------#
#Settings Views
#-------------------------------------------------#

# Render Settings Page
def settings(request):
    return render(request, 'settings.html')


# Render Export to CSV Page
def export_to_csv(request):
    return render(request, 'export_to_csv.html')


# Export Supplier DB to CSV
def export_suppliers(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="suppliers.csv"'

    writer = csv.writer(response)
    writer.writerow(['name','accNumber', 'contact', 'phone', 'email', 'comment'])

    suppliers = Supplier.objects.all().values_list('name','accNumber', 'contact', 'phone', 'email', 'comment')
    for supplier in suppliers:
        writer.writerow(supplier)
    return response


# Export Raw Material DB to CSV
def export_raw_materials(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="raw_materials.csv"'

    writer = csv.writer(response)
    writer.writerow(['description', 'code', 'supplier', 'categorie', 'price', 'quantity', 'unit'])

    raw_materials = RawMaterial.objects.all().values_list('description', 'code', 'supplier', 'categorie', 'price', 'quantity', 'unit')
    for raw_material in raw_materials:
        writer.writerow(raw_material)
    return response


# Export Base Recipes DB to CSV
def export_base_recipes(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="base_recipes.csv"'

    writer = csv.writer(response)
    writer.writerow(['name', 'ingredients', 'recipe_yeld', 'yield_unit'])

    base_recipes = Base_recipes.objects.all().values_list('name', 'ingredients', 'recipe_yeld', 'yield_unit')
    for base_recipe in base_recipes:
        writer.writerow(base_recipe)
    return response


# Export Products DB to CSV
def export_products(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'

    writer = csv.writer(response)
    writer.writerow(['name', 'categorie', 'ingredients', 'recipe_yeld', 'yield_unit', 'price', 'vat'])

    products = Product.objects.all().values_list('name', 'categorie', 'ingredients', 'recipe_yeld', 'yield_unit', 'price', 'vat')
    for product in products:
        writer.writerow(product)
    return response


# List all web app users
def userslist(request):
    template_name = 'users.html'
    context = {}
    User = get_user_model()
    users = list(User.objects.all())
    context['users'] = users
    return render(request, template_name, context)


# Create a new user
class User_Create(CreateView):
    model = get_user_model()
    fields = '__all__'
    template_name = 'new_user.html'
    success_url = reverse_lazy('control:users')
   

# Update a User
class User_Update(UpdateView):
    model = get_user_model()
    fields = '__all__'
    template_name = 'user.html'
    success_url = reverse_lazy('control:users')
    
# Delete a User
class User_Delete(DeleteView):
    model = RawMaterial
    template_name = 'delete_user.html'
    success_url = reverse_lazy('control:users')