# Generated by Django 2.2.8 on 2021-10-16 11:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0026_workflows_workflowstages'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkflowConfiguration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interviewer', models.CharField(max_length=100, null=True)),
                ('is_automation', models.BooleanField(null=True)),
                ('shortlist', models.FloatField(null=True)),
                ('onhold', models.FloatField(null=True)),
                ('reject', models.FloatField(null=True)),
                ('workflow_stage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflow_stage_id', to='company.WorkflowStages')),
            ],
        ),
    ]
