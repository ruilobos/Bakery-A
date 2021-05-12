from django.db import models
from django.urls import reverse


#-------------------------------------#
# Create RawMaterial DB.
#-------------------------------------#
class RawMaterial(models.Model):
    UNIT_CHOICES = (
        ('KG', 'kg'),
        ('L', 'l'),
        ('UNIT', 'unit'),
    )
    CATEGORY_CHOICES = (
        ('BEVERAGE', 'Beverage'),
        ('BREAD', 'Bread'),
        ('DAIRY & EGGS', 'Dairy & Eggs'),
        ('DRY GOODS', 'Dry Goods'),
        ('FISH', 'Fish'),
        ('FRUIT & VEG', 'Fruit & Veg'),
        ('MEAT', 'Meat'),
        ('PACKING', 'Packing'),
    )
    description = models.CharField("Description", max_length=100)
    code = models.CharField("Code", max_length=30, blank=True)
    supplier = models.ForeignKey("Supplier", on_delete=models.SET_NULL, null=True)
    categorie = models.CharField("Category", max_length=30, choices=CATEGORY_CHOICES)
    price = models.DecimalField("Price (€)", max_digits=6, decimal_places=2)
    quantity = models.CharField("Quantity", max_length=6)
    unit = models.CharField("Unit", max_length=5, choices=UNIT_CHOICES)

    def __str__(self):
        return self.description

    # URL to redirect
    def get_absolute_url(self):
        return reverse("raw_material", args=[str(self.id)])

    class Meta:
        verbose_name = "Raw Material"
        verbose_name_plural = "Raw Materials"
        ordering = ['description']
    

#-------------------------------------#
# Create Supplier DB
#-------------------------------------#
class Supplier(models.Model):
    name = models.CharField("Supplier Name", max_length=100, primary_key=True)
    accNumber = models.CharField("ACC Number",max_length=30, blank=True) 
    contact = models.CharField("Contact", max_length=30, blank=True) 
    phone = models.IntegerField("Phone Number", blank=True)
    email = models.EmailField("Email", max_length=30, blank=True)
    comment = models.CharField("Comment", max_length=100, blank=True)

    def __str__(self):
        return self.name

    # URL to redirect
    def get_absolute_url(self):
        return reverse("", args=[str(self.id)])

    class Meta:
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"
        ordering = ['name']


#-------------------------------------#
# Create Base_recipes DB
#-------------------------------------#
class Base_recipes(models.Model):
    UNIT_CHOICES = (
        ('KG', 'kg'),
        ('L', 'l'),
        ('UNIT', 'unit'),
    )
    name = models.CharField("Base Recipe Name", max_length=100)
    recipe_yeld = models.IntegerField("Recipe Yield") 
    yield_unit = models.CharField("Yield Unit", max_length=5, choices=UNIT_CHOICES)

    def __str__(self):
        return self.name

    # URL to redirect
    def get_absolute_url(self):
        return reverse("control:base_recipe", args=[str(self.id)])

    class Meta:
        verbose_name = "Base Recipe"
        verbose_name_plural = "Base Recipes"
        ordering = ['name']


#-------------------------------------#
# Create Bs_Ingredients DB
#-------------------------------------#
class Bs_Ingredients(models.Model):
    CATEGORY_CHOICES = (
        ('BEVERAGE', 'Beverage'),
        ('BREAD', 'Bread'),
        ('DAIRY & EGGS', 'Dairy & Eggs'),
        ('DRY GOODS', 'Dry Goods'),
        ('FISH', 'Fish'),
        ('FRUIT & VEG', 'Fruit & Veg'),
        ('MEAT', 'Meat'),
        ('PACKING', 'Packing'),
    )
    UNIT_CHOICES = (
        ('KG', 'kg'),
        ('L', 'l'),
        ('UNIT', 'unit'),
    )
    ingredient = models.ForeignKey("RawMaterial", on_delete=models.SET_NULL, null=True)
    base_recipe = models.ForeignKey("Base_recipes", on_delete=models.SET_NULL, null=True)
    quantity = models.DecimalField("Quantity", max_digits=5, decimal_places=3)
    unit = models.CharField("Unit", max_length=5, choices=UNIT_CHOICES)

    def __str__(self):
        return self.ingredient.description

    # URL to redirect
    def get_absolute_url(self):
        return reverse("control:base_recipe", args=[str(self.base_recipe.id)])

    # function to calculate the unit cost
    @property
    def cost(self):
        cost = "{:.2f}".format(self.quantity*self.ingredient.price)
        return cost

    class Meta:
        verbose_name = "Base Recipe Ingredient"
        verbose_name_plural = "Base Recipies Ingredients"
        ordering = ['ingredient']


#-------------------------------------#
# Create Recipe_Ingredients DB
#-------------------------------------#
class Recipe_Ingredients(models.Model):
    CATEGORY_CHOICES = (
        ('BEVERAGE', 'Beverage'),
        ('BREAD', 'Bread'),
        ('DAIRY & EGGS', 'Dairy & Eggs'),
        ('DRY GOODS', 'Dry Goods'),
        ('FISH', 'Fish'),
        ('FRUIT & VEG', 'Fruit & Veg'),
        ('MEAT', 'Meat'),
        ('PACKING', 'Packing'),
    )
    UNIT_CHOICES = (
        ('KG', 'kg'),
        ('L', 'l'),
        ('UNIT', 'unit'),
    )
    ingredient = models.ForeignKey("RawMaterial", on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey("Product", on_delete=models.SET_NULL, null=True)
    quantity = models.DecimalField("Quantity", max_digits=5, decimal_places=3)
    unit = models.CharField("Unit", max_length=5, choices=UNIT_CHOICES)

    def __str__(self):
        return self.ingredient.description

    # URL to redirect
    def get_absolute_url(self):
        return reverse("control:products", args=[str(self.product.categorie)])

    # function to calculate the unit cost
    @property
    def cost(self):
        cost = "{:.2f}".format(self.quantity*self.ingredient.price)
        return cost

    # function to calculate the net price
    @property
    def net_price(self):
        net_price = "{:.2f}".format(self.product.price*(1-self.product.vat))
        return net_price

    # function to calculate the margin percent
    @property
    def margin_percent(self):
        cost_recipe = 0
        for iten in self.ingredients.all():
            cost_recipe += (iten.quantity * iten.ingredient.price)
        unit_cost = cost_recipe/self.recipe_yeld
        margin_value = (self.price-(self.price*self.vat))-unit_cost
        net_price = self.price-(self.price*self.vat)
        margin = margin_value/net_price
        margin_percent = "{:.2f}".format(margin*100)  
        return margin_percent

    # function to calculate the margin value
    @property
    def margin_value(self):
        cost_recipe = 0
        for iten in self.ingredients.all():
            cost_recipe += (iten.quantity * iten.ingredient.price)
        unit_cost = cost_recipe/self.recipe_yeld
        margin_value = "{:.2f}".format((self.price-(self.price*self.vat))-unit_cost)
        return margin_value

    class Meta:
        verbose_name = "Recipe Ingredient"
        verbose_name_plural = "Recipe Ingredients"
        ordering = ['ingredient']


#-------------------------------------#
# Create Product DB
#-------------------------------------#
class Product(models.Model):
    UNIT_CHOICES = (
        ('KG', 'kg'),
        ('L', 'l'),
        ('UNIT', 'unit'),
    )
    CATEGORY_CHOICES = (
        ('BEVERAGES', 'Beverages'),
        ('CAKES', 'Cakes'),
        ('DESSERTS', 'Desserts'),
        ('FINANCIER & MADELEINE', 'Financier & Madeleine'),
        ('FRENCH TOASTS', 'French Toasts'),
        ('HOT FOODS', 'Hot Foods'),
        ('MACARONS', 'Macarons'),
        ('PASTRIES', 'Pastries'),
        ('SANDWICHES', 'Sandwiches'),
        ('SCONE, CREPE & PORRIDGE', 'Scone, Crepe & Porridge'),
        ('SWEETS', 'Sweets'),
    )
    name = models.CharField("Product Name", max_length=100)
    categorie = models.CharField("Category", max_length=30, choices=CATEGORY_CHOICES)
    recipe_yeld = models.DecimalField("Recipe Yield", max_digits=6, decimal_places=2) 
    yield_unit = models.CharField("Yield Unit", max_length=5, choices=UNIT_CHOICES)
    price = models.DecimalField("Selling Price (€)", max_digits=6, decimal_places=2)
    vat = models.DecimalField("VAT (%)", max_digits=6, decimal_places=2)

    def __str__(self):
        return self.name

    # URL to redirect
    def get_absolute_url(self):
        return reverse("products_categories", args=[str(self.id)])

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['name']