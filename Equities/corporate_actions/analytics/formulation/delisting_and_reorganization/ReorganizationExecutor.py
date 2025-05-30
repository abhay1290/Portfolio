from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.delisting_and_reorganization.Reorganization import Reorganization


class ReorganizationExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: Reorganization):
        super().__init__(ca)

        if not isinstance(ca, Reorganization):
            raise ValueError("Must provide a  Reorganization instance")

        self.reorganization = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
