# Generated by Django 2.2.8 on 2021-09-27 12:21

from django.db import migrations, models
import django.db.models.deletion
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0008_auto_20210927_1035'),
    ]

    operations = [
        migrations.CreateModel(
            name='InternalCandidatePortfolio',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_name', models.CharField(max_length=100)),
                ('project_link', models.CharField(max_length=100)),
                ('attachment', models.FileField(null=True, upload_to='')),
                ('description', tinymce.models.HTMLField()),
            ],
        ),
        migrations.CreateModel(
            name='InternalCandidateAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_name', models.CharField(max_length=50)),
                ('file', models.FileField(upload_to='')),
                ('internal_candidate_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='internal_candidate_attachment', to='company.InternalCandidate')),
            ],
        ),
    ]