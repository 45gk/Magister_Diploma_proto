"""
Обратная совместимость: импорт staging-моделей из models.py.
"""

from .models import (  # noqa: F401
    ApplicationTest,
    ApplicationTrain,
    Bureau,
    BureauBalance,
    CreditCardBalance,
    ETL_JUNK_FIELDS,
    InstallmentsPayments,
    PosCashBalance,
    PreviousApplication,
)
