from django.contrib import admin

from .models import AgentExplanation, BehavioralContext, Client, CreditApplication, FinancialProfile, ScoringInfo

admin.site.register(Client)
admin.site.register(FinancialProfile)
admin.site.register(BehavioralContext)
admin.site.register(CreditApplication)
admin.site.register(ScoringInfo)
admin.site.register(AgentExplanation)
