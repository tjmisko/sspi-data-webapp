class InvalidQueryError(Exception):
    """
    Raised when a query is invalid
    """
    pass

class InvalidDocumentFormatError(Exception):
    """
    Raised when an observation to be inserted into the database is missing a required 
    """
    pass

class InvalidDatabaseError(Exception):
    """
    Raised when a query is invalid
    """
    pass