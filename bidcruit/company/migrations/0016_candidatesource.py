# Generated by Django 2.2.8 on 2021-10-05 10:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0015_auto_20211004_1107'),
    ]

    operations = [
        migrations.CreateModel(
            name='CandidateSource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
    ]
