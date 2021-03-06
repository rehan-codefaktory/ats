# Generated by Django 2.2.8 on 2021-08-09 06:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('company', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShortlistedCandidates',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('candidate_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='shortlisted_candidate_id', to=settings.AUTH_USER_MODEL)),
                ('company_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='shortlisted_company_id', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
