from enum import Enum


class Environment(str, Enum):
    """
    Application environments - short form for ease of use.

    Values:
        LOCAL: Local development machine
        DEV: Development server
        STAGE: Staging/QA environment
        PROD: Production environment
    """

    LOCAL = "local"
    DEV = "dev"
    STAGE = "stage"
    PROD = "prod"

    @classmethod
    def from_string(cls, value: str) -> "Environment":
        """
        Parse environment from string (case-insensitive).

        Args:
            value: String representation of environment

        Returns:
            Environment enum value

        Raises:
            ValueError: If value is not a valid environment
        """
        value_lower = value.lower().strip()

        # Map common variations
        mapping = {
            "local": cls.LOCAL,
            "dev": cls.DEV,
            "stage": cls.STAGE,
            "prod": cls.PROD,
        }

        if value_lower not in mapping:
            valid_values = ", ".join(e.value for e in cls)
            raise ValueError(
                f"Invalid environment '{value}'. Must be one of: {valid_values}"
            )

        return mapping[value_lower]
