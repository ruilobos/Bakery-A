from django.contrib import admin
from django.urls import path
from control import views

app_name="control"

urlpatterns = [
    #-------------------------------------#
    #Dashboard Urls
    #-------------------------------------#
    path('dashboard/', views.Dashboard.as_view(), name='dashboard'),

    #-------------------------------------#
    #Raw Materials Urls
    #-------------------------------------#
    path('rw_categories/', views.rw_categories, name='rw_categories'),
    path('raw_materials/<pk>', views.RawMaterialsList.as_view(), name='raw_materials'),
    path('raw_materials/create/', views.Raw_material_Create.as_view(), name='raw_materials_create'),
    path('raw_materials/<int:pk>/update/', views.Raw_material_Update.as_view(), name='raw_materials_update'),
    path('raw_materials/<int:pk>/delete/', views.Raw_material_Delete.as_view(), name='raw_materials_delete'),

    path('suppliers/', views.SuppliersList.as_view(), name='suppliers'),
    path('suppliers/create/', views.Supplier_Create.as_view(), name='supplier_create'),
    path('suppliers/<str:pk>/update/', views.Supplier_Update.as_view(), name='supplier_update'),
    path('suppliers/<str:pk>/delete/', views.Supplier_Delete.as_view(), name='supplier_delete'),

    #-------------------------------------#
    #Base Recipes Urls
    #-------------------------------------#
    path('base_recipes/', views.Base_recipesList.as_view(), name='base_recipes'),

    path('base_recipes/ingredients/create/<int:pk>', views.Br_Ingre_Create.as_view(), name='br_ingre_create'), 
    path('base_recipes/ingredients/<int:pk>/update/', views.Br_Ingre_Update.as_view(), name='br_ingre_update'), 
    path('base_recipes/ingredients/<int:pk>/delete/', views.Br_Ingre_Delete.as_view(), name='br_ingre_delete'), 

    path('base_recipes/<int:pk>', views.Base_recipe.as_view(), name='base_recipe'),
    path('base_recipes/create/', views.Base_recipes_Create.as_view(), name='base_recipe_create'),
    path('base_recipes/<int:pk>/update/', views.Base_recipes_Update.as_view(), name='base_recipe_update'),
    path('base_recipes/<int:pk>/delete/', views.Base_recipes_Delete.as_view(), name='base_recipe_delete'),

    #-------------------------------------#
    #Products Urls
    #-------------------------------------#
    path('products/', views.products_categories, name='products_categories'),

    path('products/ingredients/create/<str:pk>', views.Pro_Ingre_Create.as_view(), name='pro_ingre_create'),
    path('products/ingredients/<int:pk>/update/', views.Pro_Ingre_Update.as_view(), name='pro_ingre_update'),
    path('products/ingredients/<int:pk>/delete/', views.Pro_Ingre_Delete.as_view(), name='pro_ingre_delete'),

    path('products/<str:pk>', views.Product_List.as_view(), name='products'),
    path('products/create/', views.Product_Create.as_view(), name='products_create'),
    path('products/<int:pk>/update/', views.Product_Update.as_view(), name='products_update'),
    path('products/<int:pk>/delete/', views.Product_Delete.as_view(), name='products_delete'), 

    #-------------------------------------#
    #Settings Urls
    #-------------------------------------#
    path('settings/', views.settings, name='settings'),

    path('settings/export_to_csv', views.export_to_csv, name='export_to_csv'),
    path('settings/export_to_csv/suppliers', views.export_suppliers, name='export_suppliers'),
    path('settings/export_to_csv/raw_materials', views.export_raw_materials, name='export_raw_materials'),
    path('settings/export_to_csv/base_recipes', views.export_base_recipes, name='export_base_recipes'),
    path('settings/export_to_csv/products', views.export_products, name='export_products'),

    path('settings/users/', views.userslist, name='users'),
    path('settings/users/create/', views.User_Create.as_view(), name='users_create'),
    path('settings/users/<int:pk>/update/', views.User_Update.as_view(), name='users_update'),
    path('settings/users/<str:pk>/delete/', views.User_Delete.as_view(), name='users_delete'),
]