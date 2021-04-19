# Generated by Django 3.2 on 2021-04-16 13:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('name', models.CharField(max_length=100, primary_key=True, serialize=False, verbose_name='Supplier Name')),
                ('accNumber', models.CharField(blank=True, max_length=30, verbose_name='ACC Number')),
                ('contact', models.CharField(blank=True, max_length=30, verbose_name='Contact')),
                ('phone', models.IntegerField(blank=True, verbose_name='Phone Number')),
                ('email', models.EmailField(blank=True, max_length=30, verbose_name='Email')),
                ('comment', models.CharField(blank=True, max_length=100, verbose_name='Comment')),
            ],
            options={
                'verbose_name': 'Supplier',
                'verbose_name_plural': 'Suppliers',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='RawMaterial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=100, verbose_name='Description')),
                ('code', models.CharField(blank=True, max_length=30, verbose_name='Code')),
                ('categorie', models.CharField(choices=[('BEVERAGE', 'Beverage'), ('BREAD', 'Bread'), ('DAIRY & EGGS', 'Dairy & Eggs'), ('DRY GOODS', 'Dry Goods'), ('FISH', 'Fish'), ('FRUIT & VEG', 'Fruit & Veg'), ('MEAT', 'Meat'), ('PACKING', 'Packing')], max_length=30, verbose_name='Category')),
                ('price', models.DecimalField(decimal_places=2, max_digits=6, verbose_name='Price (€)')),
                ('quantity', models.DecimalField(decimal_places=3, max_digits=6, verbose_name='Quantity')),
                ('unit', models.CharField(choices=[('KG', 'kg'), ('L', 'l'), ('UNIT', 'unit')], max_length=5, verbose_name='Unit')),
                ('supplier', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='control.supplier')),
            ],
            options={
                'verbose_name': 'Raw Material',
                'verbose_name_plural': 'Raw Materials',
                'ordering': ['description'],
            },
        ),
    ]
