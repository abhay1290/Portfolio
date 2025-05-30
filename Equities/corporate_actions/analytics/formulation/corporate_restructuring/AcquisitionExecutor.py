from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.corporate_restructuring.Acquisition import Acquisition


class AcquisitionExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: Acquisition):
        super().__init__(ca)

        if not isinstance(ca, Acquisition):
            raise ValueError("Must provide a Acquisition instance")

        self.acquisition = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
