# Generated by Django 3.2.7 on 2021-11-27 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0004_alter_chat_content'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='content',
            field=models.TextField(max_length=100000),
        ),
    ]