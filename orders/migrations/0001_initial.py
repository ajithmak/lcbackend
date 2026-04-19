# Generated migration for orders app (PostgreSQL)
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True
    dependencies = [
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id',              models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('code',            models.CharField(db_index=True, max_length=30, unique=True)),
                ('discount_type',   models.CharField(choices=[('percent', 'Percentage'), ('fixed', 'Fixed Amount')],
                                        default='percent', max_length=10)),
                ('discount_value',  models.DecimalField(decimal_places=2, max_digits=10)),
                ('min_order_value', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=10)),
                ('max_uses',        models.PositiveIntegerField(default=100)),
                ('used_count',      models.PositiveIntegerField(default=0)),
                ('is_active',       models.BooleanField(default=True)),
                ('valid_from',      models.DateTimeField(auto_now_add=True)),
                ('valid_until',     models.DateTimeField(blank=True, null=True)),
            ],
            options={'app_label': 'orders'},
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id',              models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('user',            models.ForeignKey(blank=True, db_index=True, null=True,
                                        on_delete=django.db.models.deletion.SET_NULL,
                                        related_name='orders', to=settings.AUTH_USER_MODEL)),
                ('name',            models.CharField(max_length=150)),
                ('email',           models.EmailField(db_index=True, max_length=254)),
                ('phone',           models.CharField(max_length=15)),
                ('address',         models.TextField()),
                ('subtotal',        models.DecimalField(decimal_places=2, max_digits=12)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=12)),
                ('total',           models.DecimalField(decimal_places=2, max_digits=12)),
                ('coupon',          models.ForeignKey(blank=True, null=True,
                                        on_delete=django.db.models.deletion.SET_NULL,
                                        related_name='orders', to='orders.coupon')),
                ('coupon_code',     models.CharField(blank=True, max_length=30)),
                ('status',          models.CharField(choices=[
                                        ('pending','Pending'), ('confirmed','Confirmed'),
                                        ('processing','Processing'), ('shipped','Shipped'),
                                        ('delivered','Delivered'), ('cancelled','Cancelled')],
                                        db_index=True, default='pending', max_length=20)),
                ('notes',           models.TextField(blank=True)),
                ('created_at',      models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at',      models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-created_at'], 'app_label': 'orders'},
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id',            models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('order',         models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                      related_name='items', to='orders.order')),
                ('product',       models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                      related_name='order_items', to='products.product')),
                ('product_name',  models.CharField(max_length=200)),
                ('product_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('quantity',      models.PositiveIntegerField(default=1)),
                ('line_total',    models.DecimalField(decimal_places=2, max_digits=12)),
            ],
            options={'app_label': 'orders'},
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['status', '-created_at'], name='idx_order_status_date'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['email'], name='idx_order_email'),
        ),
    ]
