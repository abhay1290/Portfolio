from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.rights_and_warrants.RightsIssue import RightsIssue


class RightsIssueExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: RightsIssue):
        super().__init__(ca)

        if not isinstance(ca, RightsIssue):
            raise ValueError("Must provide a  RightsIssue instance")

        self.rights_issue = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
