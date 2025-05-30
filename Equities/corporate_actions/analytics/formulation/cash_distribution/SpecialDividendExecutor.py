from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.cash_distribution.SpecialDividend import SpecialDividend


class SpecialDividendExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: SpecialDividend):
        super().__init__(ca)

        if not isinstance(ca, SpecialDividend):
            raise ValueError("Must provide a SpecialDividend instance")

        self.special_dividend = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
