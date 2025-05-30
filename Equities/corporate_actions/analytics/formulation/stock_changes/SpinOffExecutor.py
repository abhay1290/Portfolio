from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.stock_changes.SpinOff import SpinOff


class SpinOffExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: SpinOff):
        super().__init__(ca)

        if not isinstance(ca, SpinOff):
            raise ValueError("Must provide a  SpinOff instance")

        self.spin_off = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
