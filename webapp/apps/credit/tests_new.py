"""Тесты загрузчика CSV (_new)."""

import csv
import io
from django.test import SimpleTestCase

from .csv_loader_new import HomeCreditCsvLoader


class HomeCreditCsvLoaderTests(SimpleTestCase):
    def _make_csv(self, headers, rows):
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return io.BytesIO(buf.getvalue().encode('utf-8'))

    def test_load_bureau_balance(self):
        headers = ['SK_ID_BUREAU', 'MONTHS_BALANCE', 'STATUS']
        data = self._make_csv(headers, [{'SK_ID_BUREAU': '1', 'MONTHS_BALANCE': '-1', 'STATUS': '0'}])
        loader = HomeCreditCsvLoader()
        result = loader.load_stream('bureau_balance', data, source_name='test.csv')
        self.assertTrue(result.ok)
        self.assertEqual(result.row_count, 1)
        self.assertEqual(result.rows[0]['sk_id_bureau'], 1)
        self.assertEqual(result.rows[0]['months_balance'], -1)

    def test_strip_junk_helper(self):
        loader = HomeCreditCsvLoader()
        rows = [
            {
                'sk_id_curr': 100001,
                'legacy_amt_income_text': '270000.0',
                'internal_sync_token': 'PENDING',
            },
        ]
        cleaned = loader.strip_junk_from_rows('ApplicationTrain', rows)
        self.assertNotIn('legacy_amt_income_text', cleaned[0])
        self.assertNotIn('internal_sync_token', cleaned[0])
        self.assertEqual(cleaned[0]['sk_id_curr'], 100001)

    def test_validate_headers_missing(self):
        loader = HomeCreditCsvLoader()
        missing = loader.validate_headers('bureau_balance', ['SK_ID_BUREAU'])
        self.assertIn('MONTHS_BALANCE', missing)
