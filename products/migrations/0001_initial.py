# Generated migration for products app (PostgreSQL)
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id',          models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name',        models.CharField(max_length=100, unique=True)),
                ('slug',        models.SlugField(unique=True, db_index=True)),
                ('description', models.TextField(blank=True)),
                ('icon',        models.CharField(blank=True, max_length=10)),
                ('is_active',   models.BooleanField(default=True)),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
                'app_label': 'products',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id',             models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name',           models.CharField(db_index=True, max_length=200)),
                ('slug',           models.SlugField(unique=True, db_index=True)),
                ('description',    models.TextField(blank=True)),
                ('category',       models.ForeignKey(blank=True, db_index=True, null=True,
                                       on_delete=django.db.models.deletion.SET_NULL,
                                       related_name='products', to='products.category')),
                ('price',          models.DecimalField(decimal_places=2, max_digits=10)),
                ('original_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('stock',          models.PositiveIntegerField(db_index=True, default=0)),
                ('min_order',      models.PositiveIntegerField(default=1)),
                ('image',          models.ImageField(blank=True, null=True, upload_to='products/')),
                ('image_url',      models.URLField(blank=True)),
                ('is_featured',    models.BooleanField(db_index=True, default=False)),
                ('is_active',      models.BooleanField(db_index=True, default=True)),
                ('tags',           models.CharField(blank=True, max_length=500)),
                ('created_at',     models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at',     models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-created_at'],
                'app_label': 'products',
            },
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['is_active', '-created_at'], name='idx_product_active_date'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['is_active', 'is_featured'], name='idx_product_featured'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['category', 'is_active'], name='idx_product_category_active'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['price'], name='idx_product_price'),
        ),
    ]
