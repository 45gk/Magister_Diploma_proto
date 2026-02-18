from django.db import models


class Client(models.Model):
    education = models.CharField(max_length=100, blank=True)
    sex = models.CharField(max_length=10, blank=True)
    age = models.IntegerField(null=True, blank=True)
    car = models.BooleanField(default=False)
    car_type = models.BooleanField(default=False)
    income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    foreign_passport = models.BooleanField(default=False)


class FinancialProfile(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='financial_profiles')
    decline_app_cnt = models.IntegerField(default=0)
    good_work = models.BooleanField(default=False)
    bki_request_cnt = models.IntegerField(default=0)
    region_rating = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)


class BehavioralContext(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='behavioral_contexts')
    home_address = models.CharField(max_length=100, blank=True)
    work_address = models.CharField(max_length=100, blank=True)
    sna = models.CharField(max_length=100, blank=True)
    first_time = models.BooleanField(default=True)


class CreditApplication(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='applications')
    app_date = models.DateField()
    features = models.JSONField(default=dict, blank=True)


class ScoringInfo(models.Model):
    application = models.OneToOneField(CreditApplication, on_delete=models.CASCADE, related_name='scoring')
    score_bki = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    default_probability = models.DecimalField(max_digits=5, decimal_places=4)
    model_version = models.CharField(max_length=20)
    feature_importances = models.JSONField(default=dict)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    generated_at = models.DateTimeField(auto_now_add=True)


class AgentExplanation(models.Model):
    application = models.OneToOneField(CreditApplication, on_delete=models.CASCADE, related_name='agent_explanation')
    mode = models.CharField(max_length=20, default='brief')
    payload = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)
