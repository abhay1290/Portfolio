from Identifier.IdentifierTypeEnum import IdentifierTypeEnum


class SecurityIdentifier:
    def __init__(self, identifier_type: IdentifierTypeEnum, identifier_value: str):
        self.identifier_type = identifier_type
        self.identifier_value = identifier_value

    # # Primary Identifiers
    # symbol = Column(String(20), nullable=False, index=True)
    # isin = Column(String(12), nullable=True, unique=True, index=True)  # International Securities Identification Number
    # cusip = Column(String(9), nullable=True, index=True)  # Committee on Uniform Securities Identification Procedures
    # sedol = Column(String(7), nullable=True, index=True)  # Stock Exchange Daily Official List
    # bloomberg_ticker = Column(String(50), nullable=True)
    # reuters_ric = Column(String(50), nullable=True)  # Reuters Instrument Code
    # local_code = Column(String(20), nullable=True)  # Local exchange code

    # # Company Information
    # company_name = Column(String(255), nullable=False)
    # company_legal_name = Column(String(255), nullable=True)
    # short_name = Column(String(100), nullable=True)
    # lei = Column(String(20), nullable=True)  # Legal Entity Identifier

    # # Classification
    # sector = Column(Enum(SectorEnum), nullable=True)
    # industry = Column(Enum(IndustryEnum), nullable=True)
    # gics_sector = Column(String(50), nullable=True)  # Global Industry Classification Standard
    # gics_industry_group = Column(String(50), nullable=True)
    # gics_industry = Column(String(50), nullable=True)
    # gics_sub_industry = Column(String(50), nullable=True)
    # sic_code = Column(String(10), nullable=True)  # Standard Industrial Classification
    # naics_code = Column(String(10), nullable=True)  # North American Industry Classification System

    def update_identifier(self, identifier_type, identifier_value):
        """
        Update the identifier type and value.

        :param identifier_type: New type of identifier
        :param identifier_value: New value of the identifier
        """
        self.identifier_type = identifier_type
        self.identifier_value = identifier_value

    def get_identifier(self):
        """Return the identifier in the format of (identifier_type, identifier_value)."""
        return self.identifier_type, self.identifier_value
