# Generated by Django 2.2.8 on 2021-08-07 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidate', '0014_auto_20210807_0851'),
    ]

    operations = [
        migrations.AddField(
            model_name='company_data_request',
            name='zip_link',
            field=models.CharField(max_length=500, null=True),
        ),
    ]
