from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.corporate_restructuring.TenderOffer import TenderOffer


class TenderOfferExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: TenderOffer):
        super().__init__(ca)

        if not isinstance(ca, TenderOffer):
            raise ValueError("Must provide a TenderOffer instance")

        self.tender_offer = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
