# Generated by Django 5.1.2 on 2024-11-02 03:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0004_alter_profile_about_me'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='ku_generation',
            field=models.PositiveSmallIntegerField(default=83),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='profile',
            name='major',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
