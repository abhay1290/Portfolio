from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.rights_and_warrants.Subscription import Subscription


class SubscriptionExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: Subscription):
        super().__init__(ca)

        if not isinstance(ca, Subscription):
            raise ValueError("Must provide a  Subscription instance")

        self.subscription = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
