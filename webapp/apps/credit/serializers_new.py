"""
Сериализаторы (_new) для API загрузки CSV и строк staging.
"""

from rest_framework import serializers

from .csv_loader_interface import CsvLoadResult
from .models import AgentExplanation, BehavioralContext, Client, CreditApplication, FinancialProfile, ScoringInfo


class ClientSerializerNew(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


class FinancialProfileSerializerNew(serializers.ModelSerializer):
    class Meta:
        model = FinancialProfile
        fields = ('decline_app_cnt', 'good_work', 'bki_request_cnt', 'region_rating')


class BehavioralContextSerializerNew(serializers.ModelSerializer):
    class Meta:
        model = BehavioralContext
        fields = ('home_address', 'work_address', 'sna', 'first_time')


class CreditApplicationCreateSerializerNew(serializers.Serializer):
    client = ClientSerializerNew()
    financial_profile = FinancialProfileSerializerNew(required=False)
    behavioral_context = BehavioralContextSerializerNew(required=False)
    application = serializers.DictField()
    features = serializers.DictField(required=False)


class ScoringInfoSerializerNew(serializers.ModelSerializer):
    class Meta:
        model = ScoringInfo
        exclude = ('id', 'application')


class AgentExplanationSerializerNew(serializers.ModelSerializer):
    class Meta:
        model = AgentExplanation
        exclude = ('id', 'application')


class CreditApplicationDetailSerializerNew(serializers.ModelSerializer):
    client = ClientSerializerNew(read_only=True)
    scoring = ScoringInfoSerializerNew(read_only=True)
    agent_explanation = AgentExplanationSerializerNew(read_only=True)

    class Meta:
        model = CreditApplication
        fields = ('id', 'app_date', 'features', 'client', 'scoring', 'agent_explanation')


class CsvLoadResultSerializerNew(serializers.Serializer):
    dataset = serializers.CharField()
    row_count = serializers.IntegerField()
    ok = serializers.BooleanField()
    errors = serializers.ListField(child=serializers.CharField())
    warnings = serializers.ListField(child=serializers.CharField(), required=False)
    junk_fields_stripped = serializers.BooleanField()
    source_name = serializers.CharField()
    preview_rows = serializers.ListField(child=serializers.DictField(), required=False)

    @staticmethod
    def from_load_result(result: CsvLoadResult, preview_limit: int = 5) -> dict:
        return {
            'dataset': result.dataset,
            'row_count': result.row_count,
            'ok': result.ok,
            'errors': result.errors,
            'warnings': result.warnings,
            'junk_fields_stripped': result.junk_fields_stripped,
            'source_name': result.source_name,
            'preview_rows': result.rows[:preview_limit],
        }
