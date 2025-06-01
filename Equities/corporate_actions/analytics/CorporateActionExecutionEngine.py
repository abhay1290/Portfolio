from Equities.corporate_actions.analytics.formulation.CorporateActionExecutorBase import CorporateActionExecutorBase
from Equities.corporate_actions.analytics.formulation.cash_distribution.DistributionExecutor import DistributionExecutor
from Equities.corporate_actions.analytics.formulation.cash_distribution.DividendExecutor import DividendExecutor
from Equities.corporate_actions.analytics.formulation.cash_distribution.ReturnOfCapitalExecutor import \
    ReturnOfCapitalExecutor
from Equities.corporate_actions.analytics.formulation.cash_distribution.SpecialDividendExecutor import \
    SpecialDividendExecutor
from Equities.corporate_actions.analytics.formulation.corporate_restructuring.AcquisitionExecutor import \
    AcquisitionExecutor
from Equities.corporate_actions.analytics.formulation.corporate_restructuring.ExchangeOfferExecutor import \
    ExchangeOfferExecutor
from Equities.corporate_actions.analytics.formulation.corporate_restructuring.MergerExecutor import MergerExecutor
from Equities.corporate_actions.analytics.formulation.corporate_restructuring.TenderOfferExecutor import \
    TenderOfferExecutor
from Equities.corporate_actions.analytics.formulation.delisting_and_reorganization.BankruptcyExecutor import \
    BankruptcyExecutor
from Equities.corporate_actions.analytics.formulation.delisting_and_reorganization.DelistingExecutor import \
    DelistingExecutor
from Equities.corporate_actions.analytics.formulation.delisting_and_reorganization.LiquidationExecutor import \
    LiquidationExecutor
from Equities.corporate_actions.analytics.formulation.delisting_and_reorganization.ReorganizationExecutor import \
    ReorganizationExecutor
from Equities.corporate_actions.analytics.formulation.rights_and_warrants.RightsIssueExecutor import RightsIssueExecutor
from Equities.corporate_actions.analytics.formulation.rights_and_warrants.SubscriptionExecutor import \
    SubscriptionExecutor
from Equities.corporate_actions.analytics.formulation.rights_and_warrants.WarrentExerciseExecutor import \
    WarrantExerciseExecutor
from Equities.corporate_actions.analytics.formulation.stock_changes.ReverseSplitExecutor import ReverseSplitExecutor
from Equities.corporate_actions.analytics.formulation.stock_changes.SpinOffExecutor import SpinOffExecutor
from Equities.corporate_actions.analytics.formulation.stock_changes.StockDividendExecutor import StockDividendExecutor
from Equities.corporate_actions.analytics.formulation.stock_changes.StockSplitExecutor import StockSplitExecutor
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


def ca_execution_engine(ca: CorporateActionBase) -> CorporateActionExecutorBase:
    # cash distribution
    if ca.action_type == CorporateActionTypeEnum.DIVIDEND:
        return DividendExecutor(ca)
    elif ca.action_type == CorporateActionTypeEnum.DISTRIBUTION:
        return DistributionExecutor(ca)
    elif ca.action_type == CorporateActionTypeEnum.RETURN_OF_CAPITAL:
        return ReturnOfCapitalExecutor(ca)
    elif ca.action_type == CorporateActionTypeEnum.SPECIAL_DIVIDEND:
        return SpecialDividendExecutor(ca)

    # corporate restructuring
    elif ca.action_type == CorporateActionTypeEnum.ACQUISITION:
        return AcquisitionExecutor(ca)
    elif ca.action_type == CorporateActionTypeEnum.EXCHANGE_OFFER:
        return ExchangeOfferExecutor(ca)
    elif ca.action_type == CorporateActionTypeEnum.MERGER:
        return MergerExecutor(ca)
    elif ca.action_type == CorporateActionTypeEnum.TENDER_OFFER:
        return TenderOfferExecutor(ca)

    # delisting/reorg
    elif ca.action_type == CorporateActionTypeEnum.BANKRUPTCY:
        return BankruptcyExecutor(ca)
    elif ca.action_type == CorporateActionTypeEnum.DELISTING:
        return DelistingExecutor(ca)
    elif ca.action_type == CorporateActionTypeEnum.LIQUIDATION:
        return LiquidationExecutor(ca)
    elif ca.action_type == CorporateActionTypeEnum.REORGANIZATION:
        return ReorganizationExecutor(ca)

    # rights and warrants
    elif ca.action_type == CorporateActionTypeEnum.RIGHTS_ISSUE:
        return RightsIssueExecutor(ca)
    elif ca.action_type == CorporateActionTypeEnum.SUBSCRIPTION:
        return SubscriptionExecutor(ca)
    elif ca.action_type == CorporateActionTypeEnum.WARRANT_EXERCISE:
        return WarrantExerciseExecutor(ca)

    # stock changes
    elif ca.action_type == CorporateActionTypeEnum.REVERSE_SPLIT:
        return ReverseSplitExecutor(ca)
    elif ca.action_type == CorporateActionTypeEnum.SPIN_OFF:
        return SpinOffExecutor(ca)
    elif ca.action_type == CorporateActionTypeEnum.STOCK_DIVIDEND:
        return StockDividendExecutor(ca)
    elif ca.action_type == CorporateActionTypeEnum.STOCK_SPLIT:
        return StockSplitExecutor(ca)
    else:
        raise ValueError(f"Unsupported corporate action type: {ca.action_type}")
