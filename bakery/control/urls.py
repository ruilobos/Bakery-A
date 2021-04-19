from django.contrib import admin
from django.urls import path
from control import views

app_name="control"

urlpatterns = [
    path('dashboard/', views.Dashboard.as_view(), name='dashboard'),

    path('rw_categories/', views.rw_categories, name='rw_categories'),
    path('raw_materials/<pk>', views.RawMaterialsList.as_view(), name='raw_materials'),
    path('raw_materials/create/', views.Raw_material_Create.as_view(), name='raw_materials_create'),
    path('raw_materials/<int:pk>/update/', views.Raw_material_Update.as_view(), name='raw_materials_update'),
    path('raw_materials/<int:pk>/delete/', views.Raw_material_Delete.as_view(), name='raw_materials_delete'),

    path('suppliers/', views.SuppliersList.as_view(), name='suppliers'),
    path('suppliers/create/', views.Supplier_Create.as_view(), name='supplier_create'),
    path('suppliers/<str:pk>/update/', views.Supplier_Update.as_view(), name='supplier_update'),
    path('suppliers/<str:pk>/delete/', views.Supplier_Delete.as_view(), name='supplier_delete'),

    path('base_recipes/', views.Base_recipesList.as_view(), name='base_recipes'),
    path('base_recipes/<int:pk>', views.Base_recipe.as_view(), name='base_recipe'),
    path('base_recipes/create/', views.Base_recipes_Create.as_view(), name='base_recipe_create'),
    path('base_recipes/create/ingredients', views.Ingredient_Create.as_view(), name='ingredient_create'),
    path('base_recipes/<int:pk>/update/', views.Base_recipes_Update.as_view(), name='base_recipe_update'),
    path('base_recipes/<int:pk>/delete/', views.Base_recipes_Delete.as_view(), name='base_recipe_delete'),

    path('products_categories/', views.products_categories, name='products_categories'),
    path('products/<str:pk>', views.Product_List.as_view(), name='products'),
    path('products/create/', views.Product_Create.as_view(), name='products_create'),
    path('products/<int:pk>/update/', views.Product_Update.as_view(), name='products_update'),
    path('products/<int:pk>/delete/', views.Product_Delete.as_view(), name='products_delete'),
]