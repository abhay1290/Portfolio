from enum import Enum

class CorporateActionEnum(Enum):
    # Mandatory Corporate Actions
    CASH_DIVIDEND = "Cash Dividend"
    STOCK_DIVIDEND = "Stock Dividend"
    SPECIAL_DIVIDEND = "Special Dividend"
    STOCK_SPLIT = "Stock Split"
    RIGHTS_ISSUE = "Rights Issue"

    MERGER = "Merger"
    ACQUISITION = "Acquisition"
    TAKEOVER = "Takeover"
    AMALGAMATION = "Amalgamation"
    SPIN_OFF = "Spin-off"
    CAPITAL_REDUCTION = "Capital Reduction"

    DELISTING = "Delisting"

    # Voluntary Corporate Actions
    SHARE_BUYBACK = "Share Buyback Repurchase Program"
    TENDER_OFFER = "Tender Offer"
    RIGHTS_ISSUE_OPTIONAL = "Rights Issue optional participation"
    WARRANT_EXERCISE = "Warrant Exercise"
    EXCHANGE_OFFER = "Exchange Offer"

    # Mandatory with Choice Corporate Actions
    DIVIDEND_OPTION = "Cash or Stock Dividend Dividend Option"
    PARTIAL_BUYBACK = "Stock Buyback with Partial Acceptance"
