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
    
    def drop_duplicates(self):
        pass

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
        Raises an error if the document is not in the valid

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
        if not "IndicatorCode":
            raise InvalidObservationFormatError(f"'IndicatorCode' is a required argument (observation {observation_number})")
        if not "Raw":
            raise InvalidObservationFormatError(f"'Raw' is a required argument (observation {observation_number})")
        if not "CollectedAt":
            raise InvalidObservationFormatError(f"'CollectedAt' is a required argument (observation {observation_number})")
        


    
    