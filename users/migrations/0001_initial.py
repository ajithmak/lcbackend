# Generated migration for users app (PostgreSQL)
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id',          models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('password',    models.CharField(max_length=128, verbose_name='password')),
                ('last_login',  models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser',models.BooleanField(default=False)),
                ('email',       models.EmailField(db_index=True, max_length=254, unique=True)),
                ('name',        models.CharField(max_length=150)),
                ('phone',       models.CharField(blank=True, max_length=15)),
                ('address',     models.TextField(blank=True)),
                ('is_active',   models.BooleanField(default=True)),
                ('is_staff',    models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('groups',      models.ManyToManyField(blank=True, related_name='user_set',
                                    related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, related_name='user_set',
                                    related_query_name='user', to='auth.permission',
                                    verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'app_label': 'users',
            },
        ),
    ]
