from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
from bson import json_util
from sspi_flask_app.models.errors import InvalidDocumentFormatError
import json
from datetime import datetime


class SSPIRawAPIData(MongoWrapper):
    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Raises an InvalidDocumentFormatError if the document is not in the
        valid:

        Valid Document Format:
            {
                "IndicatorCode": str,
                "Raw": str or dict or int or float,
                "CollectedAt": datetime,
                ...
            }
        The fields IndicatorCode, Raw, and CollectedAt are required.
        Additional fields are allowed, but not required.
        """
        self.validate_indicator_code(document, document_number)
        self.validate_raw(document, document_number)
        self.validate_collected_at(document, document_number)
        self.validate_username(document, document_number)

    def tabulate_ids(self):
        tab_ids = self._mongo_database.aggregate([
            {"$group": {
                "_id": {
                    "IndicatorCode": "$IndicatorCode",
                    "Raw": "$Raw"
                },
                "count": {"$sum": 1},
                "ids": {"$push": "$_id"}
            }},
        ])
        return json.loads(json_util.dumps(tab_ids))

    def validate_collected_at(self, document: dict, document_number: int = 0):
        # Validate CollectedAt format
        if "CollectedAt" not in document.keys():
            print(f"Document Produced an Error: {document}")
            doc_id = f"(document {document_number})"
            raise InvalidDocumentFormatError(
                f"'CollectedAt' is a required argument {doc_id}")
        if not type(document["CollectedAt"]) is str:
            print(f"Document Produced an Error: {document}")
            doc_id = f"(document {document_number})"
            raise InvalidDocumentFormatError(
                f"'CollectedAt' must be a str {(doc_id)}")

    def validate_username(self, document: dict, document_number: int = 0):
        # Validate Username format
        if "Username" not in document.keys():
            print(f"Document Produced an Error: {document}")
            doc_id = f"(document {document_number})"
            raise InvalidDocumentFormatError(
                f"'Username' is a required argument {doc_id}")
        if not type(document["Username"]) is str:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Username' must be a str (document {document_number})")

    def validate_raw(self, document: dict, document_number: int = 0):
        # Validate Raw format
        if "Raw" not in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Raw' is a required argument (document {document_number})")
        if not type(document["Raw"]) in [str, dict, int, float, list]:
            print(f"Document Produced an Error: {document}")
            doc_id = f"(document {document_number})"
            raise InvalidDocumentFormatError(
                f"'Raw' must be a string, dict, int, float, or list {doc_id}")

    def raw_insert_one(self, document, IndicatorCode, **kwargs) -> int:
        """
        Utility Function the response from an API call in the database
        - Document to be passed as a well-formed dictionary or string for entry
        into pymongo
        - IndicatorCode is the indicator code for the indicator that the
        observation is for
        """
        document = {
            "IndicatorCode": IndicatorCode,
            "Raw": document,
            "CollectedAt": datetime.now().strftime("%F %R")
        }
        document.update(kwargs)
        self.insert_one(document)
        return 1

    def raw_insert_many(self, document_list, IndicatorCode, **kwargs) -> int:
        """
        Utility Function
        - Observation to be past as a list of well form observation
        dictionaries
        - IndicatorCode is the indicator code for the indicator that the
        observation is for
        """
        for observation in document_list:
            self.raw_insert_one(observation, IndicatorCode, **kwargs)
        return len(document_list)

    def fetch_raw_data(self, IndicatorCode, **kwargs) -> list:
        """
        Utility function that handles querying the database
        """
        if not bool(self.find_one({"IndicatorCode": IndicatorCode})):
            print(f"Document Produced an Error: {IndicatorCode}")
            raise ValueError("Indicator Code not found in database")
        mongoQuery = {"IndicatorCode": IndicatorCode}
        mongoQuery.update(kwargs)
        return self.find(mongoQuery)

    def raw_data_available(self, IndicatorCode, **kwargs) -> bool:
        """
        Returns True if raw data is available for the given indicator code and
        kwargs
        """
        MongoQuery = {"IndicatorCode": IndicatorCode}
        MongoQuery.update(kwargs)
        return bool(self.find_one(MongoQuery))
