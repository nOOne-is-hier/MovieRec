# Generated by Django 4.2.4 on 2024-11-21 06:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_customuser_options_customuser_date_joined_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='phone_number',
            field=models.CharField(blank=True, help_text='사용자의 전화번호', max_length=15, null=True),
        ),
    ]