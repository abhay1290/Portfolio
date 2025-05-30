from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.model.rights_and_warrants.WarrentExercise import WarrantExercise


class WarrantExerciseExecutor(CorporateActionExecutorBase):
    def __init__(self, ca: WarrantExercise):
        super().__init__(ca)

        if not isinstance(ca, WarrantExercise):
            raise ValueError("Must provide a  WarrantExercise instance")

        self.warrant_exercise = ca

        self._validate_inputs()

    def execute(self):
        pass

    def rollback(self):
        pass
