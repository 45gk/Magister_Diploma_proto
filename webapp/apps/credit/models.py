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
    explanation = models.TextField(blank=True)
    payload = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)


"""
Исходные модели банковских систем (staging / source layer).

Соответствие файлам Kaggle Home Credit Default Risk:
  https://www.kaggle.com/competitions/home-credit-default-risk/data

Имена полей — snake_case от колонок CSV (SK_ID_CURR → sk_id_curr).
Поля с пометкой «ETL: мусор» добавлены намеренно для демонстрации очистки в пайплайне.
"""


# ---------------------------------------------------------------------------
# application_train.csv / application_test.csv
# ---------------------------------------------------------------------------


class ApplicationTrain(models.Model):
    """application_train.csv — 122 колонки, включая TARGET."""

    sk_id_curr = models.BigIntegerField(primary_key=True, db_column='SK_ID_CURR')
    target = models.SmallIntegerField(null=True, blank=True, db_column='TARGET')
    name_contract_type = models.CharField(max_length=64, blank=True, db_column='NAME_CONTRACT_TYPE')
    code_gender = models.CharField(max_length=8, blank=True, db_column='CODE_GENDER')
    flag_own_car = models.CharField(max_length=8, blank=True, db_column='FLAG_OWN_CAR')
    flag_own_realty = models.CharField(max_length=8, blank=True, db_column='FLAG_OWN_REALTY')
    cnt_children = models.IntegerField(null=True, blank=True, db_column='CNT_CHILDREN')
    amt_income_total = models.FloatField(null=True, blank=True, db_column='AMT_INCOME_TOTAL')
    amt_credit = models.FloatField(null=True, blank=True, db_column='AMT_CREDIT')
    amt_annuity = models.FloatField(null=True, blank=True, db_column='AMT_ANNUITY')
    amt_goods_price = models.FloatField(null=True, blank=True, db_column='AMT_GOODS_PRICE')
    name_type_suite = models.CharField(max_length=128, blank=True, db_column='NAME_TYPE_SUITE')
    name_income_type = models.CharField(max_length=64, blank=True, db_column='NAME_INCOME_TYPE')
    name_education_type = models.CharField(max_length=64, blank=True, db_column='NAME_EDUCATION_TYPE')
    name_family_status = models.CharField(max_length=64, blank=True, db_column='NAME_FAMILY_STATUS')
    name_housing_type = models.CharField(max_length=64, blank=True, db_column='NAME_HOUSING_TYPE')
    region_population_relative = models.FloatField(null=True, blank=True, db_column='REGION_POPULATION_RELATIVE')
    days_birth = models.IntegerField(null=True, blank=True, db_column='DAYS_BIRTH')
    days_employed = models.FloatField(null=True, blank=True, db_column='DAYS_EMPLOYED')
    days_registration = models.FloatField(null=True, blank=True, db_column='DAYS_REGISTRATION')
    days_id_publish = models.IntegerField(null=True, blank=True, db_column='DAYS_ID_PUBLISH')
    own_car_age = models.FloatField(null=True, blank=True, db_column='OWN_CAR_AGE')
    flag_mobil = models.IntegerField(null=True, blank=True, db_column='FLAG_MOBIL')
    flag_emp_phone = models.IntegerField(null=True, blank=True, db_column='FLAG_EMP_PHONE')
    flag_work_phone = models.IntegerField(null=True, blank=True, db_column='FLAG_WORK_PHONE')
    flag_cont_mobile = models.IntegerField(null=True, blank=True, db_column='FLAG_CONT_MOBILE')
    flag_phone = models.IntegerField(null=True, blank=True, db_column='FLAG_PHONE')
    flag_email = models.IntegerField(null=True, blank=True, db_column='FLAG_EMAIL')
    occupation_type = models.CharField(max_length=128, blank=True, db_column='OCCUPATION_TYPE')
    cnt_fam_members = models.FloatField(null=True, blank=True, db_column='CNT_FAM_MEMBERS')
    region_rating_client = models.IntegerField(null=True, blank=True, db_column='REGION_RATING_CLIENT')
    region_rating_client_w_city = models.IntegerField(null=True, blank=True, db_column='REGION_RATING_CLIENT_W_CITY')
    weekday_appr_process_start = models.CharField(max_length=16, blank=True, db_column='WEEKDAY_APPR_PROCESS_START')
    hour_appr_process_start = models.FloatField(null=True, blank=True, db_column='HOUR_APPR_PROCESS_START')
    reg_region_not_live_region = models.IntegerField(null=True, blank=True, db_column='REG_REGION_NOT_LIVE_REGION')
    reg_region_not_work_region = models.IntegerField(null=True, blank=True, db_column='REG_REGION_NOT_WORK_REGION')
    live_region_not_work_region = models.IntegerField(null=True, blank=True, db_column='LIVE_REGION_NOT_WORK_REGION')
    reg_city_not_live_city = models.IntegerField(null=True, blank=True, db_column='REG_CITY_NOT_LIVE_CITY')
    reg_city_not_work_city = models.IntegerField(null=True, blank=True, db_column='REG_CITY_NOT_WORK_CITY')
    live_city_not_work_city = models.IntegerField(null=True, blank=True, db_column='LIVE_CITY_NOT_WORK_CITY')
    organization_type = models.CharField(max_length=128, blank=True, db_column='ORGANIZATION_TYPE')
    ext_source_1 = models.FloatField(null=True, blank=True, db_column='EXT_SOURCE_1')
    ext_source_2 = models.FloatField(null=True, blank=True, db_column='EXT_SOURCE_2')
    ext_source_3 = models.FloatField(null=True, blank=True, db_column='EXT_SOURCE_3')
    apartments_avg = models.FloatField(null=True, blank=True, db_column='APARTMENTS_AVG')
    basementarea_avg = models.FloatField(null=True, blank=True, db_column='BASEMENTAREA_AVG')
    years_beginexpluatation_avg = models.FloatField(null=True, blank=True, db_column='YEARS_BEGINEXPLUATATION_AVG')
    years_build_avg = models.FloatField(null=True, blank=True, db_column='YEARS_BUILD_AVG')
    commonarea_avg = models.FloatField(null=True, blank=True, db_column='COMMONAREA_AVG')
    elevators_avg = models.FloatField(null=True, blank=True, db_column='ELEVATORS_AVG')
    entrances_avg = models.FloatField(null=True, blank=True, db_column='ENTRANCES_AVG')
    floorsmax_avg = models.FloatField(null=True, blank=True, db_column='FLOORSMAX_AVG')
    floorsmin_avg = models.FloatField(null=True, blank=True, db_column='FLOORSMIN_AVG')
    landarea_avg = models.FloatField(null=True, blank=True, db_column='LANDAREA_AVG')
    livingapartments_avg = models.FloatField(null=True, blank=True, db_column='LIVINGAPARTMENTS_AVG')
    livingarea_avg = models.FloatField(null=True, blank=True, db_column='LIVINGAREA_AVG')
    nonlivingapartments_avg = models.FloatField(null=True, blank=True, db_column='NONLIVINGAPARTMENTS_AVG')
    nonlivingarea_avg = models.FloatField(null=True, blank=True, db_column='NONLIVINGAREA_AVG')
    apartments_mode = models.FloatField(null=True, blank=True, db_column='APARTMENTS_MODE')
    basementarea_mode = models.FloatField(null=True, blank=True, db_column='BASEMENTAREA_MODE')
    years_beginexpluatation_mode = models.FloatField(null=True, blank=True, db_column='YEARS_BEGINEXPLUATATION_MODE')
    years_build_mode = models.FloatField(null=True, blank=True, db_column='YEARS_BUILD_MODE')
    commonarea_mode = models.FloatField(null=True, blank=True, db_column='COMMONAREA_MODE')
    elevators_mode = models.FloatField(null=True, blank=True, db_column='ELEVATORS_MODE')
    entrances_mode = models.FloatField(null=True, blank=True, db_column='ENTRANCES_MODE')
    floorsmax_mode = models.FloatField(null=True, blank=True, db_column='FLOORSMAX_MODE')
    floorsmin_mode = models.FloatField(null=True, blank=True, db_column='FLOORSMIN_MODE')
    landarea_mode = models.FloatField(null=True, blank=True, db_column='LANDAREA_MODE')
    livingapartments_mode = models.FloatField(null=True, blank=True, db_column='LIVINGAPARTMENTS_MODE')
    livingarea_mode = models.FloatField(null=True, blank=True, db_column='LIVINGAREA_MODE')
    nonlivingapartments_mode = models.FloatField(null=True, blank=True, db_column='NONLIVINGAPARTMENTS_MODE')
    nonlivingarea_mode = models.FloatField(null=True, blank=True, db_column='NONLIVINGAREA_MODE')
    apartments_medi = models.FloatField(null=True, blank=True, db_column='APARTMENTS_MEDI')
    basementarea_medi = models.FloatField(null=True, blank=True, db_column='BASEMENTAREA_MEDI')
    years_beginexpluatation_medi = models.FloatField(null=True, blank=True, db_column='YEARS_BEGINEXPLUATATION_MEDI')
    years_build_medi = models.FloatField(null=True, blank=True, db_column='YEARS_BUILD_MEDI')
    commonarea_medi = models.FloatField(null=True, blank=True, db_column='COMMONAREA_MEDI')
    elevators_medi = models.FloatField(null=True, blank=True, db_column='ELEVATORS_MEDI')
    entrances_medi = models.FloatField(null=True, blank=True, db_column='ENTRANCES_MEDI')
    floorsmax_medi = models.FloatField(null=True, blank=True, db_column='FLOORSMAX_MEDI')
    floorsmin_medi = models.FloatField(null=True, blank=True, db_column='FLOORSMIN_MEDI')
    landarea_medi = models.FloatField(null=True, blank=True, db_column='LANDAREA_MEDI')
    livingapartments_medi = models.FloatField(null=True, blank=True, db_column='LIVINGAPARTMENTS_MEDI')
    livingarea_medi = models.FloatField(null=True, blank=True, db_column='LIVINGAREA_MEDI')
    nonlivingapartments_medi = models.FloatField(null=True, blank=True, db_column='NONLIVINGAPARTMENTS_MEDI')
    nonlivingarea_medi = models.FloatField(null=True, blank=True, db_column='NONLIVINGAREA_MEDI')
    fondkapremont_mode = models.FloatField(null=True, blank=True, db_column='FONDKAPREMONT_MODE')
    housetype_mode = models.FloatField(null=True, blank=True, db_column='HOUSETYPE_MODE')
    totalarea_mode = models.FloatField(null=True, blank=True, db_column='TOTALAREA_MODE')
    wallsmaterial_mode = models.FloatField(null=True, blank=True, db_column='WALLSMATERIAL_MODE')
    emergencystate_mode = models.FloatField(null=True, blank=True, db_column='EMERGENCYSTATE_MODE')
    obs_30_cnt_social_circle = models.FloatField(null=True, blank=True, db_column='OBS_30_CNT_SOCIAL_CIRCLE')
    def_30_cnt_social_circle = models.FloatField(null=True, blank=True, db_column='DEF_30_CNT_SOCIAL_CIRCLE')
    obs_60_cnt_social_circle = models.FloatField(null=True, blank=True, db_column='OBS_60_CNT_SOCIAL_CIRCLE')
    def_60_cnt_social_circle = models.FloatField(null=True, blank=True, db_column='DEF_60_CNT_SOCIAL_CIRCLE')
    days_last_phone_change = models.FloatField(null=True, blank=True, db_column='DAYS_LAST_PHONE_CHANGE')
    flag_document_2 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_2')
    flag_document_3 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_3')
    flag_document_4 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_4')
    flag_document_5 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_5')
    flag_document_6 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_6')
    flag_document_7 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_7')
    flag_document_8 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_8')
    flag_document_9 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_9')
    flag_document_10 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_10')
    flag_document_11 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_11')
    flag_document_12 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_12')
    flag_document_13 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_13')
    flag_document_14 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_14')
    flag_document_15 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_15')
    flag_document_16 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_16')
    flag_document_17 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_17')
    flag_document_18 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_18')
    flag_document_19 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_19')
    flag_document_20 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_20')
    flag_document_21 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_21')
    amt_req_credit_bureau_hour = models.FloatField(null=True, blank=True, db_column='AMT_REQ_CREDIT_BUREAU_HOUR')
    amt_req_credit_bureau_day = models.FloatField(null=True, blank=True, db_column='AMT_REQ_CREDIT_BUREAU_DAY')
    amt_req_credit_bureau_week = models.FloatField(null=True, blank=True, db_column='AMT_REQ_CREDIT_BUREAU_WEEK')
    amt_req_credit_bureau_mon = models.FloatField(null=True, blank=True, db_column='AMT_REQ_CREDIT_BUREAU_MON')
    amt_req_credit_bureau_qrt = models.FloatField(null=True, blank=True, db_column='AMT_REQ_CREDIT_BUREAU_QRT')
    amt_req_credit_bureau_year = models.FloatField(null=True, blank=True, db_column='AMT_REQ_CREDIT_BUREAU_YEAR')

    # ETL: мусор — дубль дохода строкой из legacy-выгрузки
    legacy_amt_income_text = models.CharField(
        max_length=64, blank=True, default='',
        db_column='LEGACY_AMT_INCOME_TEXT',
        help_text='ETL: удалить; не из Kaggle, артефакт банковской системы',
    )
    # ETL: мусор — служебный маркер миграции
    internal_sync_token = models.CharField(
        max_length=128, blank=True, default='PENDING_MIGRATION',
        db_column='INTERNAL_SYNC_TOKEN',
        help_text='ETL: удалить; служебное поле АБС',
    )

    class Meta:
        db_table = 'src_application_train'
        managed = True
        verbose_name = 'Application (train)'
        verbose_name_plural = 'Applications (train)'


class ApplicationTest(models.Model):
    """application_test.csv — те же поля, что train, без TARGET."""

    sk_id_curr = models.BigIntegerField(primary_key=True, db_column='SK_ID_CURR')
    name_contract_type = models.CharField(max_length=64, blank=True, db_column='NAME_CONTRACT_TYPE')
    code_gender = models.CharField(max_length=8, blank=True, db_column='CODE_GENDER')
    flag_own_car = models.CharField(max_length=8, blank=True, db_column='FLAG_OWN_CAR')
    flag_own_realty = models.CharField(max_length=8, blank=True, db_column='FLAG_OWN_REALTY')
    cnt_children = models.IntegerField(null=True, blank=True, db_column='CNT_CHILDREN')
    amt_income_total = models.FloatField(null=True, blank=True, db_column='AMT_INCOME_TOTAL')
    amt_credit = models.FloatField(null=True, blank=True, db_column='AMT_CREDIT')
    amt_annuity = models.FloatField(null=True, blank=True, db_column='AMT_ANNUITY')
    amt_goods_price = models.FloatField(null=True, blank=True, db_column='AMT_GOODS_PRICE')
    name_type_suite = models.CharField(max_length=128, blank=True, db_column='NAME_TYPE_SUITE')
    name_income_type = models.CharField(max_length=64, blank=True, db_column='NAME_INCOME_TYPE')
    name_education_type = models.CharField(max_length=64, blank=True, db_column='NAME_EDUCATION_TYPE')
    name_family_status = models.CharField(max_length=64, blank=True, db_column='NAME_FAMILY_STATUS')
    name_housing_type = models.CharField(max_length=64, blank=True, db_column='NAME_HOUSING_TYPE')
    region_population_relative = models.FloatField(null=True, blank=True, db_column='REGION_POPULATION_RELATIVE')
    days_birth = models.IntegerField(null=True, blank=True, db_column='DAYS_BIRTH')
    days_employed = models.FloatField(null=True, blank=True, db_column='DAYS_EMPLOYED')
    days_registration = models.FloatField(null=True, blank=True, db_column='DAYS_REGISTRATION')
    days_id_publish = models.IntegerField(null=True, blank=True, db_column='DAYS_ID_PUBLISH')
    own_car_age = models.FloatField(null=True, blank=True, db_column='OWN_CAR_AGE')
    flag_mobil = models.IntegerField(null=True, blank=True, db_column='FLAG_MOBIL')
    flag_emp_phone = models.IntegerField(null=True, blank=True, db_column='FLAG_EMP_PHONE')
    flag_work_phone = models.IntegerField(null=True, blank=True, db_column='FLAG_WORK_PHONE')
    flag_cont_mobile = models.IntegerField(null=True, blank=True, db_column='FLAG_CONT_MOBILE')
    flag_phone = models.IntegerField(null=True, blank=True, db_column='FLAG_PHONE')
    flag_email = models.IntegerField(null=True, blank=True, db_column='FLAG_EMAIL')
    occupation_type = models.CharField(max_length=128, blank=True, db_column='OCCUPATION_TYPE')
    cnt_fam_members = models.FloatField(null=True, blank=True, db_column='CNT_FAM_MEMBERS')
    region_rating_client = models.IntegerField(null=True, blank=True, db_column='REGION_RATING_CLIENT')
    region_rating_client_w_city = models.IntegerField(null=True, blank=True, db_column='REGION_RATING_CLIENT_W_CITY')
    weekday_appr_process_start = models.CharField(max_length=16, blank=True, db_column='WEEKDAY_APPR_PROCESS_START')
    hour_appr_process_start = models.FloatField(null=True, blank=True, db_column='HOUR_APPR_PROCESS_START')
    reg_region_not_live_region = models.IntegerField(null=True, blank=True, db_column='REG_REGION_NOT_LIVE_REGION')
    reg_region_not_work_region = models.IntegerField(null=True, blank=True, db_column='REG_REGION_NOT_WORK_REGION')
    live_region_not_work_region = models.IntegerField(null=True, blank=True, db_column='LIVE_REGION_NOT_WORK_REGION')
    reg_city_not_live_city = models.IntegerField(null=True, blank=True, db_column='REG_CITY_NOT_LIVE_CITY')
    reg_city_not_work_city = models.IntegerField(null=True, blank=True, db_column='REG_CITY_NOT_WORK_CITY')
    live_city_not_work_city = models.IntegerField(null=True, blank=True, db_column='LIVE_CITY_NOT_WORK_CITY')
    organization_type = models.CharField(max_length=128, blank=True, db_column='ORGANIZATION_TYPE')
    ext_source_1 = models.FloatField(null=True, blank=True, db_column='EXT_SOURCE_1')
    ext_source_2 = models.FloatField(null=True, blank=True, db_column='EXT_SOURCE_2')
    ext_source_3 = models.FloatField(null=True, blank=True, db_column='EXT_SOURCE_3')
    apartments_avg = models.FloatField(null=True, blank=True, db_column='APARTMENTS_AVG')
    basementarea_avg = models.FloatField(null=True, blank=True, db_column='BASEMENTAREA_AVG')
    years_beginexpluatation_avg = models.FloatField(null=True, blank=True, db_column='YEARS_BEGINEXPLUATATION_AVG')
    years_build_avg = models.FloatField(null=True, blank=True, db_column='YEARS_BUILD_AVG')
    commonarea_avg = models.FloatField(null=True, blank=True, db_column='COMMONAREA_AVG')
    elevators_avg = models.FloatField(null=True, blank=True, db_column='ELEVATORS_AVG')
    entrances_avg = models.FloatField(null=True, blank=True, db_column='ENTRANCES_AVG')
    floorsmax_avg = models.FloatField(null=True, blank=True, db_column='FLOORSMAX_AVG')
    floorsmin_avg = models.FloatField(null=True, blank=True, db_column='FLOORSMIN_AVG')
    landarea_avg = models.FloatField(null=True, blank=True, db_column='LANDAREA_AVG')
    livingapartments_avg = models.FloatField(null=True, blank=True, db_column='LIVINGAPARTMENTS_AVG')
    livingarea_avg = models.FloatField(null=True, blank=True, db_column='LIVINGAREA_AVG')
    nonlivingapartments_avg = models.FloatField(null=True, blank=True, db_column='NONLIVINGAPARTMENTS_AVG')
    nonlivingarea_avg = models.FloatField(null=True, blank=True, db_column='NONLIVINGAREA_AVG')
    apartments_mode = models.FloatField(null=True, blank=True, db_column='APARTMENTS_MODE')
    basementarea_mode = models.FloatField(null=True, blank=True, db_column='BASEMENTAREA_MODE')
    years_beginexpluatation_mode = models.FloatField(null=True, blank=True, db_column='YEARS_BEGINEXPLUATATION_MODE')
    years_build_mode = models.FloatField(null=True, blank=True, db_column='YEARS_BUILD_MODE')
    commonarea_mode = models.FloatField(null=True, blank=True, db_column='COMMONAREA_MODE')
    elevators_mode = models.FloatField(null=True, blank=True, db_column='ELEVATORS_MODE')
    entrances_mode = models.FloatField(null=True, blank=True, db_column='ENTRANCES_MODE')
    floorsmax_mode = models.FloatField(null=True, blank=True, db_column='FLOORSMAX_MODE')
    floorsmin_mode = models.FloatField(null=True, blank=True, db_column='FLOORSMIN_MODE')
    landarea_mode = models.FloatField(null=True, blank=True, db_column='LANDAREA_MODE')
    livingapartments_mode = models.FloatField(null=True, blank=True, db_column='LIVINGAPARTMENTS_MODE')
    livingarea_mode = models.FloatField(null=True, blank=True, db_column='LIVINGAREA_MODE')
    nonlivingapartments_mode = models.FloatField(null=True, blank=True, db_column='NONLIVINGAPARTMENTS_MODE')
    nonlivingarea_mode = models.FloatField(null=True, blank=True, db_column='NONLIVINGAREA_MODE')
    apartments_medi = models.FloatField(null=True, blank=True, db_column='APARTMENTS_MEDI')
    basementarea_medi = models.FloatField(null=True, blank=True, db_column='BASEMENTAREA_MEDI')
    years_beginexpluatation_medi = models.FloatField(null=True, blank=True, db_column='YEARS_BEGINEXPLUATATION_MEDI')
    years_build_medi = models.FloatField(null=True, blank=True, db_column='YEARS_BUILD_MEDI')
    commonarea_medi = models.FloatField(null=True, blank=True, db_column='COMMONAREA_MEDI')
    elevators_medi = models.FloatField(null=True, blank=True, db_column='ELEVATORS_MEDI')
    entrances_medi = models.FloatField(null=True, blank=True, db_column='ENTRANCES_MEDI')
    floorsmax_medi = models.FloatField(null=True, blank=True, db_column='FLOORSMAX_MEDI')
    floorsmin_medi = models.FloatField(null=True, blank=True, db_column='FLOORSMIN_MEDI')
    landarea_medi = models.FloatField(null=True, blank=True, db_column='LANDAREA_MEDI')
    livingapartments_medi = models.FloatField(null=True, blank=True, db_column='LIVINGAPARTMENTS_MEDI')
    livingarea_medi = models.FloatField(null=True, blank=True, db_column='LIVINGAREA_MEDI')
    nonlivingapartments_medi = models.FloatField(null=True, blank=True, db_column='NONLIVINGAPARTMENTS_MEDI')
    nonlivingarea_medi = models.FloatField(null=True, blank=True, db_column='NONLIVINGAREA_MEDI')
    fondkapremont_mode = models.FloatField(null=True, blank=True, db_column='FONDKAPREMONT_MODE')
    housetype_mode = models.FloatField(null=True, blank=True, db_column='HOUSETYPE_MODE')
    totalarea_mode = models.FloatField(null=True, blank=True, db_column='TOTALAREA_MODE')
    wallsmaterial_mode = models.FloatField(null=True, blank=True, db_column='WALLSMATERIAL_MODE')
    emergencystate_mode = models.FloatField(null=True, blank=True, db_column='EMERGENCYSTATE_MODE')
    obs_30_cnt_social_circle = models.FloatField(null=True, blank=True, db_column='OBS_30_CNT_SOCIAL_CIRCLE')
    def_30_cnt_social_circle = models.FloatField(null=True, blank=True, db_column='DEF_30_CNT_SOCIAL_CIRCLE')
    obs_60_cnt_social_circle = models.FloatField(null=True, blank=True, db_column='OBS_60_CNT_SOCIAL_CIRCLE')
    def_60_cnt_social_circle = models.FloatField(null=True, blank=True, db_column='DEF_60_CNT_SOCIAL_CIRCLE')
    days_last_phone_change = models.FloatField(null=True, blank=True, db_column='DAYS_LAST_PHONE_CHANGE')
    flag_document_2 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_2')
    flag_document_3 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_3')
    flag_document_4 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_4')
    flag_document_5 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_5')
    flag_document_6 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_6')
    flag_document_7 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_7')
    flag_document_8 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_8')
    flag_document_9 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_9')
    flag_document_10 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_10')
    flag_document_11 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_11')
    flag_document_12 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_12')
    flag_document_13 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_13')
    flag_document_14 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_14')
    flag_document_15 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_15')
    flag_document_16 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_16')
    flag_document_17 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_17')
    flag_document_18 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_18')
    flag_document_19 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_19')
    flag_document_20 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_20')
    flag_document_21 = models.IntegerField(null=True, blank=True, db_column='FLAG_DOCUMENT_21')
    amt_req_credit_bureau_hour = models.FloatField(null=True, blank=True, db_column='AMT_REQ_CREDIT_BUREAU_HOUR')
    amt_req_credit_bureau_day = models.FloatField(null=True, blank=True, db_column='AMT_REQ_CREDIT_BUREAU_DAY')
    amt_req_credit_bureau_week = models.FloatField(null=True, blank=True, db_column='AMT_REQ_CREDIT_BUREAU_WEEK')
    amt_req_credit_bureau_mon = models.FloatField(null=True, blank=True, db_column='AMT_REQ_CREDIT_BUREAU_MON')
    amt_req_credit_bureau_qrt = models.FloatField(null=True, blank=True, db_column='AMT_REQ_CREDIT_BUREAU_QRT')
    amt_req_credit_bureau_year = models.FloatField(null=True, blank=True, db_column='AMT_REQ_CREDIT_BUREAU_YEAR')

    export_batch_label = models.CharField(
        max_length=32, blank=True, default='BATCH_UNKNOWN',
        db_column='EXPORT_BATCH_LABEL',
        help_text='ETL: удалить; метка выгрузки из АБС',
    )

    class Meta:
        db_table = 'src_application_test'
        managed = True
        verbose_name = 'Application (test)'
        verbose_name_plural = 'Applications (test)'


# ---------------------------------------------------------------------------
# bureau.csv
# ---------------------------------------------------------------------------


class Bureau(models.Model):
    """bureau.csv — 17 колонок Kaggle + служебный мусор."""

    sk_id_bureau = models.BigIntegerField(primary_key=True, db_column='SK_ID_BUREAU')
    sk_id_curr = models.ForeignKey(
        ApplicationTrain,
        on_delete=models.DO_NOTHING,
        db_column='SK_ID_CURR',
        related_name='bureau_records',
    )
    credit_active = models.CharField(max_length=32, blank=True, db_column='CREDIT_ACTIVE')
    credit_currency = models.CharField(max_length=32, blank=True, db_column='CREDIT_CURRENCY')
    days_credit = models.IntegerField(null=True, blank=True, db_column='DAYS_CREDIT')
    credit_day_overdue = models.IntegerField(null=True, blank=True, db_column='CREDIT_DAY_OVERDUE')
    days_credit_enddate = models.FloatField(null=True, blank=True, db_column='DAYS_CREDIT_ENDDATE')
    days_enddate_fact = models.FloatField(null=True, blank=True, db_column='DAYS_ENDDATE_FACT')
    amt_credit_max_overdue = models.FloatField(null=True, blank=True, db_column='AMT_CREDIT_MAX_OVERDUE')
    cnt_credit_prolong = models.IntegerField(null=True, blank=True, db_column='CNT_CREDIT_PROLONG')
    amt_credit_sum = models.FloatField(null=True, blank=True, db_column='AMT_CREDIT_SUM')
    amt_credit_sum_debt = models.FloatField(null=True, blank=True, db_column='AMT_CREDIT_SUM_DEBT')
    amt_credit_sum_limit = models.FloatField(null=True, blank=True, db_column='AMT_CREDIT_SUM_LIMIT')
    amt_credit_sum_overdue = models.FloatField(null=True, blank=True, db_column='AMT_CREDIT_SUM_OVERDUE')
    credit_type = models.CharField(max_length=64, blank=True, db_column='CREDIT_TYPE')
    days_credit_update = models.IntegerField(null=True, blank=True, db_column='DAYS_CREDIT_UPDATE')
    amt_annuity = models.FloatField(null=True, blank=True, db_column='AMT_ANNUITY')

    # ETL: мусор — дублирующий ключ из старой системы
    old_sys_bureau_ref = models.CharField(
        max_length=64, blank=True, default='',
        db_column='OLD_SYS_BUREAU_REF',
        help_text='ETL: удалить; legacy FK',
    )

    class Meta:
        db_table = 'src_bureau'
        managed = True


# ---------------------------------------------------------------------------
# bureau_balance.csv
# ---------------------------------------------------------------------------


class BureauBalance(models.Model):
    """bureau_balance.csv — SK_ID_BUREAU, MONTHS_BALANCE, STATUS."""

    id = models.BigAutoField(primary_key=True)
    sk_id_bureau = models.ForeignKey(
        Bureau,
        on_delete=models.DO_NOTHING,
        db_column='SK_ID_BUREAU',
        related_name='balances',
    )
    months_balance = models.IntegerField(db_column='MONTHS_BALANCE')
    status = models.CharField(max_length=8, blank=True, db_column='STATUS')
    # ETL: мусор — «сырой» статус до нормализации
    raw_status_dump = models.TextField(
        blank=True, default='',
        db_column='RAW_STATUS_DUMP',
        help_text='ETL: удалить; неструктурированный хвост из выгрузки',
    )

    class Meta:
        db_table = 'src_bureau_balance'
        managed = True
        unique_together = [('sk_id_bureau', 'months_balance')]


# ---------------------------------------------------------------------------
# previous_application.csv
# ---------------------------------------------------------------------------


class PreviousApplication(models.Model):
    """previous_application.csv — 37 колонок."""

    sk_id_prev = models.BigIntegerField(primary_key=True, db_column='SK_ID_PREV')
    sk_id_curr = models.ForeignKey(
        ApplicationTrain,
        on_delete=models.DO_NOTHING,
        db_column='SK_ID_CURR',
        related_name='previous_applications',
    )
    name_contract_type = models.CharField(max_length=64, blank=True, db_column='NAME_CONTRACT_TYPE')
    amt_annuity = models.FloatField(null=True, blank=True, db_column='AMT_ANNUITY')
    amt_application = models.FloatField(null=True, blank=True, db_column='AMT_APPLICATION')
    amt_credit = models.FloatField(null=True, blank=True, db_column='AMT_CREDIT')
    amt_down_payment = models.FloatField(null=True, blank=True, db_column='AMT_DOWN_PAYMENT')
    amt_goods_price = models.FloatField(null=True, blank=True, db_column='AMT_GOODS_PRICE')
    weekday_appr_process_start = models.CharField(max_length=16, blank=True, db_column='WEEKDAY_APPR_PROCESS_START')
    hour_appr_process_start = models.FloatField(null=True, blank=True, db_column='HOUR_APPR_PROCESS_START')
    flag_last_appl_per_contract = models.CharField(max_length=8, blank=True, db_column='FLAG_LAST_APPL_PER_CONTRACT')
    nflag_last_appl_in_day = models.IntegerField(null=True, blank=True, db_column='NFLAG_LAST_APPL_IN_DAY')
    rate_down_payment = models.FloatField(null=True, blank=True, db_column='RATE_DOWN_PAYMENT')
    rate_interest_primary = models.FloatField(null=True, blank=True, db_column='RATE_INTEREST_PRIMARY')
    rate_interest_privileged = models.FloatField(null=True, blank=True, db_column='RATE_INTEREST_PRIVILEGED')
    name_cash_loan_purpose = models.CharField(max_length=64, blank=True, db_column='NAME_CASH_LOAN_PURPOSE')
    name_contract_status = models.CharField(max_length=64, blank=True, db_column='NAME_CONTRACT_STATUS')
    days_decision = models.IntegerField(null=True, blank=True, db_column='DAYS_DECISION')
    name_payment_type = models.CharField(max_length=64, blank=True, db_column='NAME_PAYMENT_TYPE')
    code_reject_reason = models.CharField(max_length=64, blank=True, db_column='CODE_REJECT_REASON')
    name_type_suite = models.CharField(max_length=128, blank=True, db_column='NAME_TYPE_SUITE')
    name_client_type = models.CharField(max_length=64, blank=True, db_column='NAME_CLIENT_TYPE')
    name_goods_category = models.CharField(max_length=64, blank=True, db_column='NAME_GOODS_CATEGORY')
    name_portfolio = models.CharField(max_length=64, blank=True, db_column='NAME_PORTFOLIO')
    name_product_type = models.CharField(max_length=64, blank=True, db_column='NAME_PRODUCT_TYPE')
    channel_type = models.CharField(max_length=64, blank=True, db_column='CHANNEL_TYPE')
    sellerplace_area = models.IntegerField(null=True, blank=True, db_column='SELLERPLACE_AREA')
    name_seller_industry = models.CharField(max_length=64, blank=True, db_column='NAME_SELLER_INDUSTRY')
    cnt_payment = models.FloatField(null=True, blank=True, db_column='CNT_PAYMENT')
    name_yield_group = models.CharField(max_length=64, blank=True, db_column='NAME_YIELD_GROUP')
    product_combination = models.CharField(max_length=64, blank=True, db_column='PRODUCT_COMBINATION')
    days_first_drawing = models.FloatField(null=True, blank=True, db_column='DAYS_FIRST_DRAWING')
    days_first_due = models.FloatField(null=True, blank=True, db_column='DAYS_FIRST_DUE')
    days_last_due_1st_version = models.FloatField(null=True, blank=True, db_column='DAYS_LAST_DUE_1ST_VERSION')
    days_last_due = models.FloatField(null=True, blank=True, db_column='DAYS_LAST_DUE')
    days_termination = models.FloatField(null=True, blank=True, db_column='DAYS_TERMINATION')
    nflag_insured_on_approval = models.IntegerField(null=True, blank=True, db_column='NFLAG_INSURED_ON_APPROVAL')

    class Meta:
        db_table = 'src_previous_application'
        managed = True


# ---------------------------------------------------------------------------
# installments_payments.csv
# ---------------------------------------------------------------------------


class InstallmentsPayments(models.Model):
    """installments_payments.csv — 7 колонок."""

    id = models.BigAutoField(primary_key=True)
    sk_id_prev = models.ForeignKey(
        PreviousApplication,
        on_delete=models.DO_NOTHING,
        db_column='SK_ID_PREV',
        related_name='installments',
    )
    num_instalment_version = models.IntegerField(db_column='NUM_INSTALMENT_VERSION')
    num_instalment_number = models.IntegerField(db_column='NUM_INSTALMENT_NUMBER')
    days_instalment = models.IntegerField(null=True, blank=True, db_column='DAYS_INSTALMENT')
    days_entry_payment = models.FloatField(null=True, blank=True, db_column='DAYS_ENTRY_PAYMENT')
    amt_instalment = models.FloatField(null=True, blank=True, db_column='AMT_INSTALMENT')
    amt_payment = models.FloatField(null=True, blank=True, db_column='AMT_PAYMENT')

    # ETL: мусор — номер строки в файле выгрузки (часто заполнен некорректно)
    source_file_row_no = models.FloatField(
        null=True, blank=True, default=0.0,
        db_column='SOURCE_FILE_ROW_NO',
        help_text='ETL: удалить; артефакт CSV-импорта',
    )

    class Meta:
        db_table = 'src_installments_payments'
        managed = True
        unique_together = [
            ('sk_id_prev', 'num_instalment_version', 'num_instalment_number'),
        ]


# ---------------------------------------------------------------------------
# credit_card_balance.csv
# ---------------------------------------------------------------------------


class CreditCardBalance(models.Model):
    """credit_card_balance.csv — 23 колонки."""

    id = models.BigAutoField(primary_key=True)
    sk_id_prev = models.ForeignKey(
        PreviousApplication,
        on_delete=models.DO_NOTHING,
        db_column='SK_ID_PREV',
        related_name='credit_card_balances',
    )
    sk_id_curr = models.ForeignKey(
        ApplicationTrain,
        on_delete=models.DO_NOTHING,
        db_column='SK_ID_CURR',
        related_name='credit_card_balances',
    )
    months_balance = models.IntegerField(db_column='MONTHS_BALANCE')
    amt_balance = models.FloatField(null=True, blank=True, db_column='AMT_BALANCE')
    amt_credit_limit_actual = models.FloatField(null=True, blank=True, db_column='AMT_CREDIT_LIMIT_ACTUAL')
    amt_drawings_atm_current = models.FloatField(null=True, blank=True, db_column='AMT_DRAWINGS_ATM_CURRENT')
    amt_drawings_current = models.FloatField(null=True, blank=True, db_column='AMT_DRAWINGS_CURRENT')
    amt_drawings_other_current = models.FloatField(null=True, blank=True, db_column='AMT_DRAWINGS_OTHER_CURRENT')
    amt_drawings_pos_current = models.FloatField(null=True, blank=True, db_column='AMT_DRAWINGS_POS_CURRENT')
    amt_inst_min_regularity = models.FloatField(null=True, blank=True, db_column='AMT_INST_MIN_REGULARITY')
    amt_payment_current = models.FloatField(null=True, blank=True, db_column='AMT_PAYMENT_CURRENT')
    amt_payment_total_current = models.FloatField(null=True, blank=True, db_column='AMT_PAYMENT_TOTAL_CURRENT')
    amt_receivable_principal = models.FloatField(null=True, blank=True, db_column='AMT_RECEIVABLE_PRINCIPAL')
    amt_recivable = models.FloatField(null=True, blank=True, db_column='AMT_RECIVABLE')
    amt_total_receivable = models.FloatField(null=True, blank=True, db_column='AMT_TOTAL_RECEIVABLE')
    cnt_drawings_atm_current = models.FloatField(null=True, blank=True, db_column='CNT_DRAWINGS_ATM_CURRENT')
    cnt_drawings_current = models.FloatField(null=True, blank=True, db_column='CNT_DRAWINGS_CURRENT')
    cnt_drawings_other_current = models.FloatField(null=True, blank=True, db_column='CNT_DRAWINGS_OTHER_CURRENT')
    cnt_drawings_pos_current = models.FloatField(null=True, blank=True, db_column='CNT_DRAWINGS_POS_CURRENT')
    cnt_instalment_mature_cum = models.FloatField(null=True, blank=True, db_column='CNT_INSTALMENT_MATURE_CUM')
    name_contract_status = models.CharField(max_length=64, blank=True, db_column='NAME_CONTRACT_STATUS')
    sk_dpd = models.IntegerField(null=True, blank=True, db_column='SK_DPD')
    sk_dpd_def = models.IntegerField(null=True, blank=True, db_column='SK_DPD_DEF')

    class Meta:
        db_table = 'src_credit_card_balance'
        managed = True
        unique_together = [('sk_id_prev', 'months_balance')]


# ---------------------------------------------------------------------------
# POS_CASH_balance.csv
# ---------------------------------------------------------------------------


class PosCashBalance(models.Model):
    """POS_CASH_balance.csv — 8 колонок Kaggle."""

    id = models.BigAutoField(primary_key=True)
    sk_id_prev = models.ForeignKey(
        PreviousApplication,
        on_delete=models.DO_NOTHING,
        db_column='SK_ID_PREV',
        related_name='pos_cash_balances',
    )
    sk_id_curr = models.ForeignKey(
        ApplicationTrain,
        on_delete=models.DO_NOTHING,
        db_column='SK_ID_CURR',
        related_name='pos_cash_balances',
    )
    months_balance = models.IntegerField(db_column='MONTHS_BALANCE')
    cnt_instalment = models.FloatField(null=True, blank=True, db_column='CNT_INSTALMENT')
    cnt_instalment_future = models.FloatField(null=True, blank=True, db_column='CNT_INSTALMENT_FUTURE')
    name_contract_status = models.CharField(max_length=64, blank=True, db_column='NAME_CONTRACT_STATUS')
    sk_dpd = models.IntegerField(null=True, blank=True, db_column='SK_DPD')
    sk_dpd_def = models.IntegerField(null=True, blank=True, db_column='SK_DPD_DEF')

    # ETL: мусор — комментарий оператора из АБС
    abs_operator_note = models.CharField(
        max_length=255, blank=True, default='',
        db_column='ABS_OPERATOR_NOTE',
        help_text='ETL: удалить; не используется в аналитике',
    )

    class Meta:
        db_table = 'src_pos_cash_balance'
        managed = True
        unique_together = [('sk_id_prev', 'months_balance')]


# Список полей-мусора для ETL (whitelist очистки)
ETL_JUNK_FIELDS = {
    'ApplicationTrain': ('legacy_amt_income_text', 'internal_sync_token'),
    'ApplicationTest': ('export_batch_label',),
    'Bureau': ('old_sys_bureau_ref',),
    'BureauBalance': ('raw_status_dump',),
    'InstallmentsPayments': ('source_file_row_no',),
    'PosCashBalance': ('abs_operator_note',),
}
