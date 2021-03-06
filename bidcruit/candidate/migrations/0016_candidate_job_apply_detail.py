# Generated by Django 2.2.8 on 2021-10-18 08:12

import candidate.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('candidate', '0015_company_data_request_zip_link'),
    ]

    operations = [
        migrations.CreateModel(
            name='candidate_job_apply_detail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gender', models.CharField(max_length=10)),
                ('resume', models.FileField(max_length=500, null=True, upload_to=candidate.models.resume_path_handler)),
                ('contact', models.CharField(max_length=100)),
                ('skill', models.CharField(max_length=100, null=True)),
                ('designation', models.CharField(max_length=100, null=True)),
                ('notice', models.CharField(max_length=100, null=True)),
                ('current_work', models.CharField(max_length=100, null=True)),
                ('ctc', models.CharField(max_length=100, null=True)),
                ('expectedctc', models.CharField(max_length=100, null=True)),
                ('total_exper', models.CharField(max_length=100, null=True)),
                ('candidate_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='candidate_job_apply', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
