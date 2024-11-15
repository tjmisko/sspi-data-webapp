from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper


class SSPIPartialAPIData(MongoWrapper):

    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        """
        self.validate_country_code(document, document_number)
        self.validate_indicator_code(document, document_number)
        self.validate_year(document, document_number)
        self.validate_intermediates(document, document_number)
