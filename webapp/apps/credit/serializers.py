from rest_framework import serializers

from .models import AgentExplanation, BehavioralContext, Client, CreditApplication, FinancialProfile, ScoringInfo


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


class FinancialProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialProfile
        fields = ('decline_app_cnt', 'good_work', 'bki_request_cnt', 'region_rating')


class BehavioralContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = BehavioralContext
        fields = ('home_address', 'work_address', 'sna', 'first_time')


class CreditApplicationCreateSerializer(serializers.Serializer):
    client = ClientSerializer()
    financial_profile = FinancialProfileSerializer(required=False)
    behavioral_context = BehavioralContextSerializer(required=False)
    application = serializers.DictField()
    features = serializers.DictField(required=False)


class ScoringInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoringInfo
        exclude = ('id', 'application')


class AgentExplanationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentExplanation
        exclude = ('id', 'application')


class CreditApplicationDetailSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    scoring = ScoringInfoSerializer(read_only=True)
    agent_explanation = AgentExplanationSerializer(read_only=True)

    class Meta:
        model = CreditApplication
        fields = ('id', 'app_date', 'features', 'client', 'scoring', 'agent_explanation')
