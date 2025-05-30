from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.delisting_and_reorganization.Delisting import Delisting


class DelistingExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: Delisting):
        super().__init__(ca)

        if not isinstance(ca, Delisting):
            raise ValueError("Must provide a  Delisting instance")

        self.delisting = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
