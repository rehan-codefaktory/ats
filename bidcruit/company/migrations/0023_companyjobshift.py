# Generated by Django 2.2.8 on 2021-10-14 14:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('company', '0022_auto_20211014_1420'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyJobShift',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(default=False)),
                ('company_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='company_shift', to=settings.AUTH_USER_MODEL)),
                ('job_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_id', to='company.JobCreation')),
                ('job_shift_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_shift_id', to='company.JobShift')),
            ],
        ),
    ]