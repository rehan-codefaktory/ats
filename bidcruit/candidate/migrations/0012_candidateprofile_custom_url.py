# Generated by Django 2.2.8 on 2021-07-30 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidate', '0011_auto_20210721_0624'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidateprofile',
            name='custom_url',
            field=models.CharField(max_length=300, null=True),
        ),
    ]