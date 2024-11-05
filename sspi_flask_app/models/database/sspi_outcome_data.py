from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper


class SSPIOutcomeData(MongoWrapper):
    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Raises an InvalidDocumentFormatError if the document is not in the
        valid format

        Valid Document Format:
            {
                "CountryCode": str,
                "IntermediateCode": str,
                "Year": int,
                "Value": float,
                "Unit": str
            }
        Additional fields are allowed but not required
        """
        self.validate_country_code(document, document_number)
        self.validate_intermediate_code(document, document_number)
        self.validate_year(document, document_number)
        self.validate_value(document, document_number)
        self.validate_unit(document, document_number)