from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.stock_changes.StockSplit import StockSplit


class StockSplitExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: StockSplit):
        super().__init__(ca)

        if not isinstance(ca, StockSplit):
            raise ValueError("Must provide a  StockSplit instance")

        self.stock_split = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
