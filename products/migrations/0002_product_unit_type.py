from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='unit_type',
            field=models.CharField(
                max_length=20,
                blank=True,
                default='',
                choices=[
                    ('box',    'Box'),
                    ('pkt',    'Packet'),
                    ('piece',  'Piece'),
                    ('set',    'Set'),
                    ('dozen',  'Dozen'),
                    ('bundle', 'Bundle'),
                    ('roll',   'Roll'),
                ],
                help_text='Packaging unit displayed on the product (e.g. Box, Packet, Piece)',
            ),
        ),
    ]
