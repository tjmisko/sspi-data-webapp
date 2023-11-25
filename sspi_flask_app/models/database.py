from datetime import datetime
import json

from bson import ObjectId
from .errors import InvalidObservationFormatError
class MongoWrapper:
    def __init__(self, mongo_database):
        self._mongo_database = mongo_database
        self.name = mongo_database.name
    
    def validate_document_format(self, document: dict, observation_number:int=None):
        if not "IndicatorCode":
            raise InvalidObservationFormatError(f"IndicatorCode is a required argument (observation {observation_number})")
        return type(document) is dict
    
    def validate_documents_format(self, documents: list):
        return all([self.validate_document_format(document, i) for i, document in enumerate(documents)])
    
    def find_one(self, query):
        return self._mongo_database.find_many(query)
    
    def find(self, query):
        return self._mongo_database.find(query)

    def insert_one(self, document):
        self.validate_document_format(document)
        return self._mongo_database.insert_one(document)
    
    def insert_many(self, documents):
        self.validate_documents_format(documents)
        return self._mongo_database.insert_many(documents)
    
    def delete_one(self, query):
        return self._mongo_database.delete_one(query)
    
    def delete_many(self, query):
        return self._mongo_database.delete_many(query)
    
    def count_duplicates(self):
        """
        Returns a list of dictionaries which counts the number of times an observation with
        duplicate identifiers appears in the database
        """
        agg = self._mongo_database.aggregate([
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
        return json.loads(agg)

    def drop_duplicates(self):
        agg = self._mongo_database.aggregate([
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
        agg = json.loads(agg)
        id_delete_list = [ObjectId(str(oid["$oid"])) for oid in sum([obs["ids"][1:] for obs in agg],[])]
        print(id_delete_list)
        count = self._mongo_database.delete_many({"_id": {"$in": id_delete_list}}).deleted_count

    def sample(self, n: int, query:dict={}):
        """
        Draws n observations from the database at random, optionally filtered by query
        """
        return self._mongo_database.aggregate([{"$match": query}, {"$sample": {"size": n}}])

class SSPIRawAPIData(MongoWrapper):
    def __init__(self, mongo_database):
        super().__init__(mongo_database)
    
    def validate_document_format(self, document: dict, observation_number:int=None):
        """
        Raises an Invaliderror if the document is not in the valid

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
        if not "IndicatorCode" in document.keys():
            raise InvalidObservationFormatError(f"'IndicatorCode' is a required argument (observation {observation_number})")
        if not "Raw" in document.keys():
            raise InvalidObservationFormatError(f"'Raw' is a required argument (observation {observation_number})")
        if not "CollectedAt":
            raise InvalidObservationFormatError(f"'CollectedAt' is a required argument (observation {observation_number})")
        if not type(document["IndicatorCode"]) is str:
            raise InvalidObservationFormatError(f"'IndicatorCode' must be a string (observation {observation_number})")
        if not len(document["IndicatorCode"]) == 6:
            raise InvalidObservationFormatError(f"'IndicatorCode' must be 6 characters long (observation {observation_number})")
        if not type(document["Raw"]) in [str, dict, int, float]:
            raise InvalidObservationFormatError(f"'Raw' must be a string, dict, int, or float (observation {observation_number})")
        if not type(document["CollectedAt"]) is datetime:
            raise InvalidObservationFormatError(f"'CollectedAt' must be a datetime (observation {observation_number})")
    
    def drop_duplicates(self):
        agg = self._mongo_database.aggregate([
            {"$group": {
                "_id": {
                    "IndicatorCode": {"$getField": {"field": "IndicatorCode", "input": "collection-info"}},
                    "observation": "$observation"
                },
                "count": {"$sum": 1},
                "ids": {"$push": "$_id"}
            }},
        ])