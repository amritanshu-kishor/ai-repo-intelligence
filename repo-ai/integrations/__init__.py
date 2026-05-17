"""
Integration layer for connecting repo-ai orchestration with parser-workflow backend.
Provides safe, modular connectors with fallback handling.
"""

__all__ = ["parser_connector", "ParserConnector", "ParserUnavailableError"]

from integrations.parser_connector import (
    parser_connector,
    ParserConnector,
    ParserUnavailableError,
    ParserConnectorError,
    InvalidGraphDataError,
)

# Made with Bob
