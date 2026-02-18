from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('education', models.CharField(blank=True, max_length=100)),
                ('sex', models.CharField(blank=True, max_length=10)),
                ('age', models.IntegerField(blank=True, null=True)),
                ('car', models.BooleanField(default=False)),
                ('car_type', models.BooleanField(default=False)),
                ('income', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('foreign_passport', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='CreditApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app_date', models.DateField()),
                ('features', models.JSONField(blank=True, default=dict)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='credit.client')),
            ],
        ),
        migrations.CreateModel(
            name='BehavioralContext',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('home_address', models.CharField(blank=True, max_length=100)),
                ('work_address', models.CharField(blank=True, max_length=100)),
                ('sna', models.CharField(blank=True, max_length=100)),
                ('first_time', models.BooleanField(default=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='behavioral_contexts', to='credit.client')),
            ],
        ),
        migrations.CreateModel(
            name='FinancialProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('decline_app_cnt', models.IntegerField(default=0)),
                ('good_work', models.BooleanField(default=False)),
                ('bki_request_cnt', models.IntegerField(default=0)),
                ('region_rating', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='financial_profiles', to='credit.client')),
            ],
        ),
        migrations.CreateModel(
            name='ScoringInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score_bki', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('default_probability', models.DecimalField(decimal_places=4, max_digits=5)),
                ('model_version', models.CharField(max_length=20)),
                ('feature_importances', models.JSONField(default=dict)),
                ('confidence', models.DecimalField(decimal_places=4, default=0.0, max_digits=5)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('application', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='scoring', to='credit.creditapplication')),
            ],
        ),
        migrations.CreateModel(
            name='AgentExplanation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mode', models.CharField(default='brief', max_length=20)),
                ('payload', models.JSONField(default=dict)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('application', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='agent_explanation', to='credit.creditapplication')),
            ],
        ),
    ]
