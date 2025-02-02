from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
from sspi_flask_app.models.errors import InvalidDocumentFormatError


class SSPICleanAPIData(MongoWrapper):

    def validate_document_format(self, document: dict, document_number: int = 0):
        self.validate_country_code(document, document_number)
        self.validate_indicator_code(document, document_number)
        self.validate_year(document, document_number)
        self.validate_value(document, document_number)
        self.validate_score(document, document_number)
        self.validate_unit(document, document_number)

    def validate_score(self, document: dict, document_number: int = 0):
        # Validate Score format
        if "Score" not in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Score' is a required argument (document {document_number})")
        if not type(document["Score"]) in [int, float]:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Score' must be a float or integer (document {document_number})")
        if "Score" not in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Score' is a required argument (document {document_number})")
        if not type(document["Score"]) in [int, float]:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Score' must be a float or integer (document {document_number})")
