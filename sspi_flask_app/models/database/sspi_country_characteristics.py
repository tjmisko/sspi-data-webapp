from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper


class SSPICountryCharacteristics(MongoWrapper):
    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Raises an InvalidDocumentFormatError if the document is not in the
        valid format

        Valid Document Format:
            {
                "CountryCode": str,
                "IntemediateCode": str,
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

    def fetch_population_data(self, InterMediateCode, Country, Year, **kwargs) -> list:
        """
        Utility function which returns population of country in specific year
        """
        query = {"IntermediateCode": InterMediateCode, "CountryCode": Country, "Year": Year}
        if not bool(self.find_one(query)):
            print(f"Population data for {Country} is not stored, will set population to 0 for observation dropping")
            return 0
        mongoQuery = query
        mongoQuery.update(kwargs)
        population = self.find_one(mongoQuery).get("Value")
        return population 
