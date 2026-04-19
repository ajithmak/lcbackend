from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupon',
            name='excluded_category_slugs',
            field=models.CharField(
                max_length=500,
                blank=True,
                default='gift-boxes,combo-packs',
                help_text='Comma-separated category slugs excluded from this coupon. E.g. gift-boxes,combo-packs',
            ),
        ),
    ]
