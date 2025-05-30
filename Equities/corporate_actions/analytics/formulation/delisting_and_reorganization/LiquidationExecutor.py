from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.delisting_and_reorganization.Liquidation import Liquidation


class LiquidationExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: Liquidation):
        super().__init__(ca)

        if not isinstance(ca, Liquidation):
            raise ValueError("Must provide a  Liquidation instance")

        self.liquidation = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
