from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.stock_changes.StockDividend import StockDividend


class StockDividendExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: StockDividend):
        super().__init__(ca)

        if not isinstance(ca, StockDividend):
            raise ValueError("Must provide a  StockDividend instance")

        self.stock_dividend = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
