# Generated by Django 2.2.8 on 2021-09-24 09:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('candidate', '0015_company_data_request_zip_link'),
        ('company', '0004_internalcandidate_internalcandidateeducation_internalcandidateexperience'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobcreation',
            name='industry_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='industry_type_id', to='candidate.IndustryType'),
        ),
    ]
