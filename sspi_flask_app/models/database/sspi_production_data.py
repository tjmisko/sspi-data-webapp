from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper


class SSPIProductionData(MongoWrapper):

    def __init__(self, mongo_database):
        self._mongo_database = mongo_database
        self._mongo_database.create_index(
            [("CCode", 1), ("ICode", 1), ("Year", 1)])
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
        pass
