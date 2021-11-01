# Generated by Django 2.2.8 on 2021-10-04 07:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('candidate', '0015_company_data_request_zip_link'),
        ('company', '0013_remove_internalcandidateexperience_notice_period'),
    ]

    operations = [
        migrations.CreateModel(
            name='InternalCandidateAddedSkill',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='InternalCandidateSkillUserMap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('custom_added_skills', models.ManyToManyField(null=True, related_name='internal_candidate_skill_user_map', to='company.InternalCandidateAddedSkill')),
                ('internal_candidate_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='internal_candidate_skill_user_id', to='company.InternalCandidate')),
                ('skills', models.ManyToManyField(null=True, related_name='internal_candidate_skill_user_map', to='candidate.Skill')),
            ],
        ),
    ]