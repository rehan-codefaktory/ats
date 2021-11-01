# Generated by Django 2.2.8 on 2021-10-18 08:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('company', '0031_jobcreation_is_publish'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppliedCadidate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='apllied_cadidate_id', to=settings.AUTH_USER_MODEL)),
                ('job_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='apllied_job_id', to='company.JobCreation')),
            ],
        ),
    ]
