from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.cash_distribution.ReturnOfCapital import ReturnOfCapital


class ReturnOfCapitalExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: ReturnOfCapital):
        super().__init__(ca)

        if not isinstance(ca, ReturnOfCapital):
            raise ValueError("Must provide a ReturnOfCapital instance")

        self.return_of_capital = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
