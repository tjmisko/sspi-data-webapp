from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper


class SSPIScoreData(MongoWrapper):

    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        """
        self.validate_country_code(document, document_number)
        self.validate_item_code(document, document_number)
        self.validate_year(document, document_number)
        self.validate_score(document, document_number)
