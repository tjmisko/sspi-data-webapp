from datetime import datetime
import json
from bson import ObjectId, json_util
from .errors import InvalidDocumentFormatError

class MongoWrapper:
    def __init__(self, mongo_database):
        self._mongo_database = mongo_database
        self.name = mongo_database.name
    
    def find_one(self, query):
        return self._mongo_database.find_one(query)
    
    def find(self, query):
        return json.loads(json_util.dumps(self._mongo_database.find(query)))

    def find(self, query, options={}):
        return json.loads(json_util.dumps(self._mongo_database.find(query, options)))

    def insert_one(self, document):
        self.validate_document_format(document)
        return self._mongo_database.insert_one(document)
    
    def insert_many(self, documents):
        self.validate_documents_format(documents)
        return self._mongo_database.insert_many(documents, ordered=False)
    
    def delete_one(self, query):
        return self._mongo_database.delete_one(query)
    
    def delete_many(self, query):
        return self._mongo_database.delete_many(query)

    def count_documents(self, query):
        return self._mongo_database.count_documents(query)
    
    def tabulate_ids(self):
        """
        Returns a list of documents with counts of the number of times a document with
        duplicate identifiers appears.

        For example, if all documents are unique, count will be 1 for all documents.
        """
        tab_ids = self._mongo_database.aggregate([
            {"$group": {
                "_id": {
                    "IndicatorCode": "$IndicatorCode",
                    "YEAR": "$YEAR",
                    "CountryCode": "$CountryCode"
                },
                "count": {"$sum": 1},
                "ids": {"$push": "$_id"}
            }},
        ])
        return json.loads(json_util.dumps(tab_ids))

    def drop_duplicates(self):
        """
        Deletes all duplicate documents from the database and returns a count of deleted documents
        """
        tab_ids= self.tabulate_ids()
        id_delete_list = [ObjectId(str(oid["$oid"])) for oid in sum([obs["ids"][1:] for obs in tab_ids],[])]
        count = self._mongo_database.delete_many({"_id": {"$in": id_delete_list}}).deleted_count
        return count

    def sample(self, n: int, query:dict={}):
        """
        Draws n documents from the database at random, optionally filtered by query
        """
        return self._mongo_database.aggregate([{"$match": query}, {"$sample": {"size": n}}])
    
    def validate_document_format(self, document: dict, document_number:int=0):
        """
        Raises an InvalidDocumentFormatError if the document is not in the valid format
        
        Overridden in with specific validation functions in child classes built from atomic validator functions below
        Default Valid Document Format:
            {
                "IndicatorCode": "BIODIV", (type: str, length: 6, case: upper)
                "CountryCode": "COU", (type: str, length: 3, case: upper)
                "Year": 2015, (type: int, length: 4, gt: 1900, lt: 2030)
                "Value": 42.3005 (float or int)
                "Unit": "MILLION_HA", (type: str) 
                "Intermediates": {
                    "TERRST": 9.7, (float or int)
                    "FRSHWT": 9.7, (float or int)
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
        self.validate_intermediates(document, document_number)
    
    def validate_documents_format(self, documents:list):
        if type(documents) is not list:
            raise InvalidDocumentFormatError(f"Type of documents must be a list -- received {type(documents)}")
        return all([self.validate_document_format(document, document_number=i) for i, document in enumerate(documents)])
    
    # Validator functions
    def validate_indicator_code(self, document: dict, document_number:int=0):
        # Validate IndicatorCode format
        if not "IndicatorCode" in document.keys():
            raise InvalidDocumentFormatError(f"'IndicatorCode' is a required argument (document {document_number})")
        if not len(document["IndicatorCode"]) == 6:
            raise InvalidDocumentFormatError(f"'IndicatorCode' must be 6 characters long (document {document_number})")
        if not type(document["IndicatorCode"]) is str:
            raise InvalidDocumentFormatError(f"'IndicatorCode' must be a string (document {document_number})")
        if not document["IndicatorCode"].isupper():
            raise InvalidDocumentFormatError(f"'IndicatorCode' must be uppercase (document {document_number})")
    
    def validate_country_code(self, document: dict, document_number:int=0):
        # Validate CountryCode format
        if not "CountryCode" in document.keys():
            raise InvalidDocumentFormatError(f"'CountryCode' is a required argument (document {document_number})")
        if not len(document["CountryCode"]) == 3:
            raise InvalidDocumentFormatError(f"'CountryCode' must be 3 characters long (document {document_number})")
        if not type(document["CountryCode"]) is str:
            raise InvalidDocumentFormatError(f"'CountryCode' must be a string (document {document_number})")
        if not document["CountryCode"].isupper():
            raise InvalidDocumentFormatError(f"'CountryCode' must be uppercase (document {document_number})")
    
    def validate_year(self, document: dict, document_number:int=0):
        # Validate Year format
        if not "Year" in document.keys():
            raise InvalidDocumentFormatError(f"'Year' is a required argument (document {document_number})")
        if not type(document["Year"]) is int:
            raise InvalidDocumentFormatError(f"'Year' must be an integer (document {document_number})")
        if not 1900 < document["Year"] < 2030:
            raise InvalidDocumentFormatError(f"'Year' must be between 1900 and 2030 (document {document_number})")
    
    def validate_value(self, document: dict, document_number:int=0):
        # Validate Value format
        if not "Value" in document.keys():
            raise InvalidDocumentFormatError(f"'Value' is a required argument (document {document_number})")
        if not type(document["Value"]) in [int, float]:
            raise InvalidDocumentFormatError(f"'Value' must be a float or integer (document {document_number})")
    
    def validate_unit(self, document: dict, document_number:int=0):
        # Validate Unit format
        if not "Unit" in document.keys():
            raise InvalidDocumentFormatError(f"'Unit' is a required argument (document {document_number})")
        if not type(document["Unit"]) is str:
            raise InvalidDocumentFormatError(f"'Unit' must be a string (document {document_number})")
    
    def validate_intermediates(self, document:dict, document_number:int=0):
        if "Intermediates" in document.keys():
            if not type(document["Intermediates"]) is dict:
                raise InvalidDocumentFormatError(f"'Intermediates' must be a dictionary (document {document_number})")
            for key, value in document["Intermediates"].items():
                if not type(key) is str:
                    raise InvalidDocumentFormatError(f"'Intermediates' keys must be strings (document {document_number})")
                if len(key) != 6:
                    raise InvalidDocumentFormatError(f"'Intermediates' keys must be 6 characters long (document {document_number})")
                if not key.isupper():
                    raise InvalidDocumentFormatError(f"'Intermediates' keys must be uppercase (document {document_number})")
                if not type(value) in [float, int]:
                    raise InvalidDocumentFormatError(f"'Intermediates' values must be floats or integers (document {document_number})")

class SSPIRawAPIData(MongoWrapper):
    
    def validate_document_format(self, document: dict, document_number:int=None):
        """
        Raises an InvalidDocumentFormatError if the document is not in the valid

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

    def tabulate_ids(self, documents: list):
        tab_ids= self._mongo_database.aggregate([
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

    def validate_document_format(self, document: dict, document_number:int=0):

    def validate_collected_at(self, document: dict, document_number:int=None):
        # Validate CollectedAt format
        if not "CollectedAt" in document.keys():
            raise InvalidDocumentFormatError(f"'CollectedAt' is a required argument (document {document_number})")
        if not type(document["CollectedAt"]) is datetime:
            raise InvalidDocumentFormatError(f"'CollectedAt' must be a datetime (document {document_number})")
    
    def validate_username(self, document: dict, document_number:int=None):
        # Validate Username format
        if not "Username" in document.keys():
            raise InvalidDocumentFormatError(f"'Username' is a required argument (document {document_number})")
        if not type(document["Username"]) is str:
            raise InvalidDocumentFormatError(f"'Username' must be a str (document {document_number})")
    
    def validate_raw(self, document: dict, document_number:int=0):
        # Validate Raw format
        if not "Raw" in document.keys():
            raise InvalidDocumentFormatError(f"'Raw' is a required argument (document {document_number})")
        if not type(document["Raw"]) in [str, dict, int, float, list]:
            raise InvalidDocumentFormatError(f"'Raw' must be a string, dict, int, float, or list (document {document_number})")

class SSPIMetadata(MongoWrapper):
    
    def validate_document_format(self, document: dict, document_number:int=None):
        """
        Raises an InvalidDocumentFormatError if the document is not in the valid

        Valid Document Format:
            {
                "DocumentType": str,
                "Metadata": str or dict or int or float or list,
                ...
            }
        Additional fields are allowed but not required
        """
        self.validate_document_type(document, document_number)
        self.validate_metadata(document, document_number)
    
    def validate_document_type(self, document: dict, document_number:int=None):
        # Validate DocumentType format
        if not "DocumentType" in document.keys():
            raise InvalidDocumentFormatError(f"'DocumentType' is a required argument (document {document_number})")
        if not type(document["DocumentType"]) is str:
            raise InvalidDocumentFormatError(f"'DocumentType' must be a string (document {document_number})")
    
    def validate_metadata(self, document: dict, document_number:int=None):
        # Validate Metadata format
        if not "Metadata" in document.keys():
            raise InvalidDocumentFormatError(f"'Metadata' is a required argument (document {document_number})")
        if not type(document["Metadata"]) in [str, dict, int, float, list]:
            raise InvalidDocumentFormatError(f"'Metadata' must be a string, dict, int, float, or list (document {document_number})")
