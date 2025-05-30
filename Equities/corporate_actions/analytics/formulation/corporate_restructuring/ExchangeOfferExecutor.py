from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.corporate_restructuring.ExchangeOffer import ExchangeOffer


class ExchangeOfferExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: ExchangeOffer):
        super().__init__(ca)

        if not isinstance(ca, ExchangeOffer):
            raise ValueError("Must provide a ExchangeOffer instance")

        self.exchange_offer = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
