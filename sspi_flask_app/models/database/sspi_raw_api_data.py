from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
from bson import json_util
import hashlib
from sspi_flask_app.models.errors import InvalidDocumentFormatError
import json
from datetime import datetime
import logging

log = logging.getLogger(__name__)


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

    def raw_insert_one(self, document: list | str | dict, IndicatorCode, **kwargs) -> int:
        """
        Utility Function the response from an API call in the database
        - Document to be passed as a well-formed dictionary or string for entry
        into pymongo
        - IndicatorCode is the indicator code for the indicator that the
        observation is for
        - Implements automatic fragmentation to handle strings which are too large
        """
        byte_max = self.maximum_document_size_bytes
        if isinstance(document, str) and len(document) > byte_max:
            num_fragments = (len(document) + byte_max - 1) // byte_max
            fragment_group_id = hashlib.blake2b(document.encode('utf-8')).hexdigest()
            for i in range(num_fragments):
                obs = {
                    "IndicatorCode": IndicatorCode,
                    "Raw": document[byte_max * i:byte_max * i + byte_max],
                    "CollectedAt": datetime.now().strftime("%F %R")
                }
                obs.update(kwargs)
                obs.update({
                    "FragmentGroupID": f"{IndicatorCode}_{fragment_group_id}",
                    "FragmentNumber": i,
                    "FragmentTotal": num_fragments,
                })
                self.insert_one(obs)
            return num_fragments
        obs = {
            "IndicatorCode": IndicatorCode,
            "Raw": document,
            "CollectedAt": datetime.now().strftime("%F %R")
        }
        obs.update(kwargs)
        self.insert_one(obs)
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
            msg = (
                "No Documents with IndicatorCode " f"{IndicatorCode} in "
                "sspi_raw_api_data. Do you forget to run collect?"
            )
            raise ValueError(msg)
        mongoQuery = {"IndicatorCode": IndicatorCode}
        mongoQuery.update(kwargs)
        raw_data = self.find(mongoQuery)
        fragment_dict = {}
        defragged_raw = []
        for obs in raw_data:
            frag_gid = obs.get("FragmentGroupID", "")
            if not frag_gid:
                defragged_raw.append(obs)
                continue
            if not fragment_dict.get(frag_gid, None):
                fragment_dict[frag_gid] = []
            fragment_dict[obs["FragmentGroupID"]].append(obs)
        for k, v in fragment_dict.items():
            log.info(f"Reassembling Fragments for Fragment {k}")
            v.sort(key=lambda x: x["FragmentNumber"])
            if not all([x["FragmentTotal"] == len(v) for x in v]):
                raise InvalidDocumentFormatError((
                    "Fragmentation Error! Your data is missing a fragment "
                    f"in FragmentGroup ({k})"
                ))
            raw = "".join([x["Raw"] for x in v])
            drops = ["FragmentNumber", "FragmentTotal", "Raw"]
            rebuilt = {f: data for f, data in v[0].items() if f not in drops}
            rebuilt["Raw"] = raw
            defragged_raw.append(rebuilt)
        return defragged_raw

    def raw_data_available(self, IndicatorCode, **kwargs) -> bool:
        """
        Returns True if raw data is available for the given indicator code and
        kwargs
        """
        MongoQuery = {"IndicatorCode": IndicatorCode}
        MongoQuery.update(kwargs)
        return bool(self.find_one(MongoQuery))
