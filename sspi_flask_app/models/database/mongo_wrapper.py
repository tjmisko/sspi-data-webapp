import json
from bson import ObjectId, json_util
from sspi_flask_app.models.errors import InvalidDocumentFormatError


class MongoWrapper:
    def __init__(self, mongo_database):
        self._mongo_database = mongo_database
        self.name = mongo_database.name

    def is_empty(self):
        doc_count = self._mongo_database.count_documents({})
        return doc_count == 0

    def find_one(self, query: dict) -> dict:
        cursor = self._mongo_database.find_one(query)
        return json.loads(json_util.dumps(cursor))

    def find(self, query: dict, options: dict = {}) -> list:
        cursor = self._mongo_database.find(query, options)
        return json.loads(json_util.dumps(cursor))

    def insert_one(self, document: dict) -> int:
        self.validate_document_format(document)
        self._mongo_database.insert_one(document)
        return 1

    def insert_many(self, documents: list) -> int:
        self.validate_documents_format(documents)
        return len(self._mongo_database.insert_many(documents).inserted_ids)

    def delete_one(self, query: dict) -> int:
        return self._mongo_database.delete_one(query).deleted_count

    def delete_many(self, query: dict) -> int:
        return self._mongo_database.delete_many(query).deleted_count

    def count_documents(self, query: dict) -> int:
        return self._mongo_database.count_documents(query)

    def tabulate_ids(self) -> list:
        """
        Returns a list of documents with counts of the number of
        times a document with duplicate identifiers appears.

        For example, if all documents are unique, count will be 1
        for all documents.
        """
        tab_ids = self._mongo_database.aggregate([
            {"$group": {
                "_id": {
                    "IndicatorCode": "$IndicatorCode",
                    "Year": "$Year",
                    "CountryCode": "$CountryCode"
                },
                "count": {"$sum": 1},
                "ids": {"$push": "$_id"}
            }},
        ])
        return json.loads(json_util.dumps(tab_ids))

    def drop_duplicates(self):
        """
        Deletes all duplicate documents from the database
        and returns a count of deleted documents
        """
        tab_ids = self.tabulate_ids()
        id_delete_list = [ObjectId(str(oid["$oid"])) for oid in sum(
            [obs["ids"][1:] for obs in tab_ids], [])]
        query = {"_id": {"$in": id_delete_list}}
        return self._mongo_database.delete_many(query).deleted_count

    def sample(self, n: int, query: dict = {}):
        """
        Draws n documents from the database at random, optionally filtered by
        query
        """
        return self._mongo_database.aggregate([{"$match": query}, {"$sample": {"size": n}}])

    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Raises an InvalidDocumentFormatError if the document is not in the 
        valid format

        Overridden in with specific validation functions in child classes built
        from atomic validator functions below
        Default Valid Document Format:
            {
                "IndicatorCode": "BIODIV", (type: str, length: 6, case: upper)
                "CountryCode": "COU", (type: str, length: 3, case: upper)
                "Year": 2015, (type: int, length: 4, gt: 1900, lt: 2030)
                "Value": 42.3005 (float or int)
                "Unit": "MILLION_HA", (type: str)
                "Intermediates": {
                    "TERRST": dict (see below for format)
                    "FRSHWT": dict (see below for format)
                    ...
                }
            ...
            }
        By default, additional fields are allowed
        """
        self.validate_country_code(document, document_number)
        self.validate_indicator_code(document, document_number)
        self.validate_year(document, document_number)
        self.validate_value(document, document_number)
        self.validate_unit(document, document_number)

    def validate_documents_format(self, documents: list):
        dtype = type(documents)
        if dtype is not list:
            print(f"Document Produced an Error: {documents}")
            raise InvalidDocumentFormatError(
                f"Type of documents must be a list -- received {dtype}")
        return all([self.validate_document_format(document, document_number=i) for i, document in enumerate(documents)])

    # Validator functions
    def validate_indicator_code(self, document: dict, document_number: int = 0):
        # Validate IndicatorCode format
        if "IndicatorCode" not in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'IndicatorCode' is a required argument (document {document_number})")
        if not len(document["IndicatorCode"]) == 6:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'IndicatorCode' must be 6 characters long (document {document_number})")
        if not type(document["IndicatorCode"]) is str:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'IndicatorCode' must be a string (document {document_number})")
        if not document["IndicatorCode"].isupper():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'IndicatorCode' must be uppercase (document {document_number})")

    def validate_intermediate_code(self, document: dict, document_number: int = 0):
        # Validate IndicatorCode format
        if "IntermediateCode" not in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'IntermediateCode' is a required argument (document {document_number})")
        if not len(document["IntermediateCode"]) == 6:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'IntermediateCode' must be 6 characters long (document {document_number})")
        if not type(document["IntermediateCode"]) is str:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'IntermediateCode' must be a string (document {document_number})")
        if not document["IntermediateCode"].isupper():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'IntermediateCode' must be uppercase (document {document_number})")

    def validate_country_code(self, document: dict, document_number: int = 0):
        # Validate CountryCode format
        if not "CountryCode" in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'CountryCode' is a required argument (document {document_number})")
        if not len(document["CountryCode"]) == 3:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'CountryCode' must be 3 characters long (document {document_number})")
        if not type(document["CountryCode"]) is str:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'CountryCode' must be a string (document {document_number})")
        if not document["CountryCode"].isupper():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'CountryCode' must be uppercase (document {document_number})")

    def validate_year(self, document: dict, document_number: int = 0):
        # Validate Year format
        if not "Year" in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Year' is a required argument (document {document_number})")
        if not type(document["Year"]) is int:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Year' must be an integer (document {document_number})")
        if not 1900 < document["Year"] < 2030:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Year' must be between 1900 and 2030 (document {document_number})")

    def validate_value(self, document: dict, document_number: int = 0):
        # Validate Value format
        if not "Value" in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Value' is a required argument (document {document_number})")
        if not type(document["Value"]) in [int, float]:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Value' must be a float or integer (document {document_number})")

    def validate_unit(self, document: dict, document_number: int = 0):
        # Validate Unit format
        if "Unit" not in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Unit' is a required argument (document {document_number})")
        if not type(document["Unit"]) is str:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Unit' must be a string (document {document_number})")

    def validate_intermediates(self, document: dict, document_number: int = 0):
        if "Intermediates" in document.keys():
            self.validate_intermediates_list(
                document["Intermediates"], document_number)

    def validate_intermediates_list(self, intermediates: list, document_number: int = 0):
        if not type(intermediates) is list:
            print(f"Document Produced an Error: {intermediates}")
            raise InvalidDocumentFormatError(f"'Intermediates' must be a list (document {
                                             document_number}); got type {type(intermediates)}")
        id_set = set()
        for intermediate in intermediates:
            if not type(intermediate) is dict:
                print(f"Document Produced an Error: {intermediates}")
                raise InvalidDocumentFormatError(
                    f"'Intermediates' must be a dictionary (document {document_number})")
            self.validate_intermediate_code(intermediate, document_number)
            self.validate_country_code(intermediate, document_number)
            self.validate_year(intermediate, document_number)
            self.validate_value(intermediate, document_number)
            self.validate_unit(intermediate, document_number)
            document_id = f"{intermediate['IntermediateCode']}_{
                intermediate['CountryCode']}_{intermediate['Year']}"
            if document_id in id_set:
                print(f"Document Produced an Error: {intermediates}")
                raise InvalidDocumentFormatError(
                    f"Duplicate intermediate document found (document {document_number})")
            id_set.add(document_id)


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
        if not "Score" in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Score' is a required argument (document {document_number})")
        if not type(document["Score"]) in [int, float]:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Score' must be a float or integer (document {document_number})")
        if not "Score" in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Score' is a required argument (document {document_number})")
        if not type(document["Score"]) in [int, float]:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Score' must be a float or integer (document {document_number})")