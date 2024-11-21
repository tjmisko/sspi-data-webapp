from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
from sspi_flask_app.models.errors import InvalidDocumentFormatError


class SSPIBulkData(MongoWrapper):

    def __init__(self, mongo_database):
        self._mongo_database = mongo_database
        self.name = mongo_database.name

    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Raises an InvalidDocumentFormatError if the document is not in the valid

        Valid Document Format:
            {
                "Endpoint": str,
                ...
            }
        Additional fields are allowed but not required
        """
        self.validate_source_organization(document, document_number)
        self.validate_dataset_name(document, document_number)
        self.validate_dataset_description(document, document_number)
        self.validate_raw_data(document, document_number)
        self.validate_raw_page(document, document_number)

    def validate_source_organization(self, document: dict, document_number: int = 0):
        if "SourceOrganization" not in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'SourceOrganization' is a required argument (document {document_number})")
        if not type(document["SourceOrganization"]) is str:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'SourceOrganization' must be a string (document {document_number})")

    def validate_dataset_name(self, document: dict, document_number: int = 0):
        if "DatasetName" not in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'DatasetName' is a required argument (document {document_number})")
        if not type(document["DatasetName"]) is str:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'DatasetName' must be a string (document {document_number})")
        if not len(document["DatasetName"]) > 3:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'DatasetName' must be at least 3 characters long (document {document_number})")

    def validate_dataset_description(self, document: dict, document_number: int = 0):
        if "DatasetDescription" not in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'DatasetDescription' is a required argument (document {document_number})")
        if not type(document["DatasetDescription"]) is str:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'DatasetDescription' must be a string (document {document_number})")
        if not len(document["DatasetDescription"]) > 20:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                    f"Provide a more detailed 'DatasetDescription' (document {document_number})")

    def validate_raw_data(self, document: dict, document_number: int = 0):
        if "Raw" not in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Raw' is a required argument (document {document_number})")
        if not document["Raw"]:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Raw' cannot be falsey. Did you forget to add the data to the document? (document {document_number})")

    def validate_raw_page(self, document: dict, document_number: int = 0):
        if "RawPage" not in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'RawPage' is a required argument (document {document_number})")
        if not type(document["RawPage"]) is int:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'RawPage' must be an int (document {document_number})")
