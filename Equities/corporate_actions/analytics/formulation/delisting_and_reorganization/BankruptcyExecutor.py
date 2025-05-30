from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.delisting_and_reorganization.Bankruptcy import Bankruptcy


class BankruptcyExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: Bankruptcy):
        super().__init__(ca)

        if not isinstance(ca, Bankruptcy):
            raise ValueError("Must provide a  Bankruptcy instance")

        self.bankruptcy = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
