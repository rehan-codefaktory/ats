# Generated by Django 2.2.8 on 2021-07-19 20:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidate', '0003_auto_20210719_0922'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidateprofile',
            name='resume_password',
            field=models.CharField(max_length=1000, null=True),
        ),
    ]