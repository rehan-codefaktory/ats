# Generated by Django 2.2.8 on 2021-10-14 14:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('company', '0020_delete_prerequisites'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category_job_creation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('active', models.BooleanField(default=True)),
                ('company_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='category_company_id', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Stage_list',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('active', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Template_creation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=2000)),
                ('active', models.BooleanField(default=True)),
                ('status', models.BooleanField(default=False, null=True)),
                ('created_by', models.CharField(max_length=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Template_creation_category', to='company.Category_job_creation')),
                ('company_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Template_creation_company_id', to=settings.AUTH_USER_MODEL)),
                ('stage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Template_creation_stage', to='company.Stage_list')),
            ],
        ),
        migrations.CreateModel(
            name='PreRequisites',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', tinymce.models.HTMLField()),
                ('html_data', tinymce.models.HTMLField()),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prerequisites_creation_category', to='company.Category_job_creation')),
                ('company_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prerequisites_company_id', to=settings.AUTH_USER_MODEL)),
                ('stage', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prerequisites_creation_stage', to='company.Stage_list')),
                ('template', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prerequisites_creation_temnplate', to='company.Template_creation')),
            ],
        ),
        migrations.CreateModel(
            name='JCR',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('ratio', models.IntegerField()),
                ('flag', models.CharField(max_length=10, null=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='jcr_creation_category', to='company.Category_job_creation')),
                ('company_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='jcr_company_id', to=settings.AUTH_USER_MODEL)),
                ('pid', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='jcr_id', to='company.JCR')),
                ('stage', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='jcr_creation_stage', to='company.Stage_list')),
                ('template', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='jcr_creation_temnplate', to='company.Template_creation')),
            ],
        ),
        migrations.AddField(
            model_name='category_job_creation',
            name='stage',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='company.Stage_list'),
        ),
    ]
