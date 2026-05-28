from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credit', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='agentexplanation',
            name='explanation',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
    ]
