import django.db.models.functions.text
from django.db import migrations, models

import users.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=124, verbose_name='название')),
            ],
            options={
                'verbose_name': 'навык',
                'verbose_name_plural': 'навыки',
                'ordering': (django.db.models.functions.text.Lower('name'),),
                'constraints': [models.UniqueConstraint(django.db.models.functions.text.Lower('name'), name='unique_skill_name_ci', violation_error_message='Такой навык уже существует.')],
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email')),
                ('name', models.CharField(max_length=124, verbose_name='имя')),
                ('surname', models.CharField(max_length=124, verbose_name='фамилия')),
                ('avatar', models.ImageField(upload_to='avatars/', verbose_name='аватар')),
                ('phone', models.CharField(blank=True, max_length=12, null=True, unique=True, verbose_name='телефон')),
                ('github_url', models.URLField(blank=True, verbose_name='ссылка на GitHub')),
                ('about', models.TextField(blank=True, max_length=256, verbose_name='о себе')),
                ('is_active', models.BooleanField(default=True, verbose_name='активен')),
                ('is_staff', models.BooleanField(default=False, verbose_name='администратор')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('skills', models.ManyToManyField(blank=True, related_name='users', to='users.skill', verbose_name='навыки')),
            ],
            options={
                'verbose_name': 'пользователь',
                'verbose_name_plural': 'пользователи',
            },
            managers=[
                ('objects', users.models.UserManager()),
            ],
        ),
    ]
