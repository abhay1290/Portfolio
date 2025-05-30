from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.stock_changes.ReverseSplit import ReverseSplit


class ReverseSplitExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: ReverseSplit):
        super().__init__(ca)

        if not isinstance(ca, ReverseSplit):
            raise ValueError("Must provide a  ReverseSplit instance")

        self.reverse_split = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
