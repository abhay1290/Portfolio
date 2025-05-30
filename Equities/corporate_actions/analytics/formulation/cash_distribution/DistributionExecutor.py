from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.cash_distribution.Distribution import Distribution


class DistributionExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: Distribution):
        super().__init__(ca)

        if not isinstance(ca, Distribution):
            raise ValueError("Must provide a Distribution instance")

        self.distribution = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
