from Identifier.IdentifierTypeEnum import IdentifierTypeEnum


class SecurityIdentifier:
    def __init__(self, identifier_type: IdentifierTypeEnum, identifier_value: str):
        """
        Initialize the SecurityIdentifier object.

        :param identifier_type: Type of the identifier (e.g., 'Ticker', 'ISIN', 'CUSIP')
        :param identifier_value: The actual identifier value (e.g., 'AAPL', 'US0378331005', '037833100')
        """
        self.identifier_type = identifier_type
        self.identifier_value = identifier_value

    def __str__(self):
        """Return a string representation of the identifier."""
        return f"{self.identifier_type}: {self.identifier_value}"

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

