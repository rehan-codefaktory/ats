# Generated by Django 2.2.8 on 2021-10-18 09:51

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0032_appliedcadidate'),
    ]

    operations = [
        migrations.AddField(
            model_name='appliedcadidate',
            name='create_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, max_length=200),
            preserve_default=False,
        ),
    ]
