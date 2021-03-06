# Generated by Django 2.2.8 on 2021-10-14 14:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0021_auto_20211014_1418'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='companyjobshift',
            name='company_id',
        ),
        migrations.RemoveField(
            model_name='companyjobshift',
            name='job_id',
        ),
        migrations.RemoveField(
            model_name='companyjobshift',
            name='job_shift_id',
        ),
        migrations.RemoveField(
            model_name='jcr',
            name='category',
        ),
        migrations.RemoveField(
            model_name='jcr',
            name='company_id',
        ),
        migrations.RemoveField(
            model_name='jcr',
            name='pid',
        ),
        migrations.RemoveField(
            model_name='jcr',
            name='stage',
        ),
        migrations.RemoveField(
            model_name='jcr',
            name='template',
        ),
        migrations.RemoveField(
            model_name='prerequisites',
            name='category',
        ),
        migrations.RemoveField(
            model_name='prerequisites',
            name='company_id',
        ),
        migrations.RemoveField(
            model_name='prerequisites',
            name='stage',
        ),
        migrations.RemoveField(
            model_name='prerequisites',
            name='template',
        ),
        migrations.RemoveField(
            model_name='template_creation',
            name='category',
        ),
        migrations.RemoveField(
            model_name='template_creation',
            name='company_id',
        ),
        migrations.RemoveField(
            model_name='template_creation',
            name='stage',
        ),
        migrations.DeleteModel(
            name='Category_job_creation',
        ),
        migrations.DeleteModel(
            name='CompanyJobShift',
        ),
        migrations.DeleteModel(
            name='JCR',
        ),
        migrations.DeleteModel(
            name='PreRequisites',
        ),
        migrations.DeleteModel(
            name='Stage_list',
        ),
        migrations.DeleteModel(
            name='Template_creation',
        ),
    ]
