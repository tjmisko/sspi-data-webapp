from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
from sspi_flask_app.models.errors import InvalidDocumentFormatError
import json
from bson import json_util


class SSPICleanAPIData(MongoWrapper):

    def validate_documents_format(self, documents: list):
        dtype = type(documents)
        if dtype is not list:
            print(f"Document Produced an Error: {documents}")
            raise InvalidDocumentFormatError(
                f"Type of documents must be a list -- received {dtype}")
        id_set = set()
        for i, document in enumerate(documents):
            self.validate_document_format(document, document_number=i)
            document_id = (
                f"{document['IndicatorCode']}_"
                f"{document['CountryCode']}_"
                f"{document['Year']}"
            )
            if document_id in id_set:
                lgth = len(documents)
                warning_msg = (
                    f"Document {i} of {lgth} Produced an Error: {document}\n"
                    "IndicatorCode, CountryCode, Year is not an ID!\n\t"
                    "- Typically, this means that you've forgotten to filter "
                    "on field in the raw data.\n\t- For example, your "
                    "indicator or intermediate data may be disaggregated for "
                    "Sex=Male, Sex=Female, and Sex=Total. If you have "
                    "forgotten to filter Sex correctly and have simply "
                    "dropped the Sex field, then there will be multiple "
                    "documents with the same IndicatorCode, CountryCode, and "
                    "Year (so you'd see this message)"
                )
                raise InvalidDocumentFormatError(warning_msg)
            id_set.add(document_id)

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

    def aggregate(self, pipeline, options={"_id": 0}):
        """
        Aggregates the data in the collection using the provided pipeline.
        """
        cursor = self._mongo_database.aggregate(pipeline)
        return json.loads(json_util.dumps(cursor))
