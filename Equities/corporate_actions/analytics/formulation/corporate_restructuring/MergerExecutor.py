from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.corporate_restructuring.Merger import Merger


class MergerExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: Merger):
        super().__init__(ca)

        if not isinstance(ca, Merger):
            raise ValueError("Must provide a Merger instance")

        self.merger = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
