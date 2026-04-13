import io
import unittest

from app import app
from utils import build_dashboard_payload, clean_transactions


class FlaskAppSmokeTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_routes_return_success(self):
        for path in ["/", "/dashboard", "/api/dashboard"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, msg=path)

    def test_upload_flow_imports_csv(self):
        with open("dataset/sample_transactions.csv", "rb") as sample_file:
            response = self.client.post(
                "/",
                data={"csv_file": (io.BytesIO(sample_file.read()), "sample_transactions.csv")},
                content_type="multipart/form-data",
                follow_redirects=True,
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Imported", response.get_data(as_text=True))

    def test_clean_transactions_output(self):
        df = clean_transactions("dataset/sample_transactions.csv")
        required_columns = {
            "date",
            "amount",
            "merchant",
            "merchant_group",
            "transaction_type",
            "is_subscription",
        }
        self.assertTrue(required_columns.issubset(df.columns))
        self.assertGreater(len(df), 0)

    def test_dashboard_payload_uses_dataframe_values(self):
        df = clean_transactions("dataset/sample_transactions.csv")
        payload = build_dashboard_payload(df)

        self.assertEqual(payload["total_transactions"], len(df))
        self.assertAlmostEqual(payload["total_spending"], float(df["amount"].sum()), places=2)
        self.assertIn("health_score", payload)
        self.assertIn("health_label", payload)


if __name__ == "__main__":
    unittest.main()
