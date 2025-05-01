from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper


class SSPIPanelData(MongoWrapper):
    """
    This class is used to handle the generation of Panel Charts on the fly
    It inherits from the SSPICleanAPIData class.
    """
    def validate_document_format(self, document: dict, document_number: int = 0):
        self.validate_country_code(document, document_number)
        self.validate_year(document, document_number)
