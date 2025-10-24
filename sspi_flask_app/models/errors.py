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

class DataMetadataMismatchError(Exception):
    """
    Raised when there is a mismatch between metadata and data order in SSPI class
    """
    pass

class MethodologyFileError(Exception):
    """
    Raised when there is an error with the methodology file
    """
    pass

class DatasetFileError(Exception):
    """
    Raised when there is an error with the methodology file
    """
    pass

class InvalidSeriesTypeError(Exception):
    """
    Raised when a series_code has no valid series type associated with it
    """
    pass

class AnalysisFileError(Exception):
    """
    Raised when there is an error with the methodology file
    """
    pass
