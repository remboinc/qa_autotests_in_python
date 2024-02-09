import pytest
import logging
import allure
from src.cabinet_datas import Endpoints
from src.cabinet_tag_functions import get_finalized_money, get_transactions_dict


class TestBalanceAndFinalizedMoney:
    def __init__(self, headers, error_tolerance_individual=0.3, error_tolerance_total=0.1):
        self.headers = headers
        self.error_tolerance_individual = error_tolerance_individual
        self.error_tolerance_total = error_tolerance_total
        self.discrepancies = []

    def get_finalized_money_data(self):
        return get_finalized_money(headers=self.headers, endpoint=Endpoints.api_stats)

    def get_transactions_data(self):
        return get_transactions_dict(
            headers=self.headers,
            endpoint=Endpoints.all_transactions,
        )

    def check_individual_values(self, expected_value, actual_value, user_id):
        individual_tolerance = expected_value * self.error_tolerance_individual
        if abs(expected_value - actual_value) > 0.1:
            try:
                assert abs(expected_value - actual_value) <= individual_tolerance, \
                    f"User {user_id}: values do not match within 30% tolerance: expected {expected_value}, actual {actual_value}"
            except AssertionError as error:
                logging.error(f"Assertion failed: {error}")
                self.discrepancies.append(str(error))

    def check_total_values(self, total_expected_value, total_actual_value):
        total_tolerance = total_expected_value * self.error_tolerance_total

        try:
            assert abs(total_expected_value - total_actual_value) <= total_tolerance, \
                f"Total values do not match within 10% tolerance: expected {total_expected_value}, actual {total_actual_value}"
        except AssertionError as error:
            logging.error(f"Failed: {error}")
            allure.attach(str(error), name="Assertion Error", attachment_type=allure.attachment_type.TEXT)
            self.discrepancies.append(str(error))

    def run_test(self, headers):
        self.headers = headers
        transactions_dict = self.get_transactions_data()
        finalized_money = self.get_finalized_money_data()

        total_expected_value = 0
        total_actual_value = 0

        for user_id in transactions_dict:
            if user_id in finalized_money:
                expected_value = transactions_dict[user_id]
                actual_value = finalized_money[user_id]

                self.check_individual_values(expected_value, actual_value, user_id)

                total_expected_value += expected_value
                total_actual_value += actual_value

        self.check_total_values(total_expected_value, total_actual_value)

        if self.discrepancies:
            raise AssertionError("Test failed due to discrepancies. Check the log for details.")


@pytest.mark.usefixtures("synchronized_test")
@allure.title("ПРОД!! Метрика finalized_money совпадает с балансом у всех пабов")
@allure.severity(allure.severity_level.CRITICAL)
def test_balance_and_finalized_money(get_prod_authorization_headers):
    test_instance = TestBalanceAndFinalizedMoney(get_prod_authorization_headers)
    test_instance.run_test(get_prod_authorization_headers)
