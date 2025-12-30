"""Input validation utilities for user inputs"""

from src.core.errors import ValidationError
from src.core.logger import setup_logger

logger = setup_logger('cadet.validation')

MAX_QUESTION_LENGTH = 1000


def validate_user_input(user_input: str, field_name: str = "input") -> str:
    """Validate and sanitize user input

    Args:
        user_input: Raw user input string
        field_name: Field name for error messages

    Returns:
        Sanitized input string

    Raises:
        ValidationError: If input is invalid
    """
    if not isinstance(user_input, str):
        logger.error(f"{field_name} is not a string: {type(user_input)}")
        raise ValidationError(f"{field_name} must be a string")

    # Strip whitespace
    sanitized = user_input.strip()

    # Check if empty
    if not sanitized:
        logger.warning(f"{field_name} is empty after stripping")
        raise ValidationError(f"{field_name} cannot be empty")

    # Check length
    if len(sanitized) > MAX_QUESTION_LENGTH:
        logger.warning(f"{field_name} exceeds max length: {len(sanitized)} > {MAX_QUESTION_LENGTH}")
        raise ValidationError(
            f"{field_name} is too long (max {MAX_QUESTION_LENGTH} characters)"
        )

    # Check for null bytes
    if '\x00' in sanitized:
        logger.error(f"{field_name} contains null bytes")
        raise ValidationError(f"{field_name} contains invalid characters")

    logger.debug(f"{field_name} validated successfully: {len(sanitized)} chars")
    return sanitized
