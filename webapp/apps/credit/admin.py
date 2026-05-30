from django.contrib import admin
from django.apps import apps

from .models import AgentExplanation, BehavioralContext, Client, CreditApplication, FinancialProfile, ScoringInfo
from .models import *

# Получаем модели текущего приложения (замените 'имя_вашего_приложения')
app_models = apps.get_app_config('credit').get_models()

for model in app_models:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass

# admin.site.register(Client)
# admin.site.register(FinancialProfile)
# admin.site.register(BehavioralContext)
# admin.site.register(CreditApplication)
# admin.site.register(ScoringInfo)
# admin.site.register(AgentExplanation)
# admin.site.register(ApplicationTrain)

