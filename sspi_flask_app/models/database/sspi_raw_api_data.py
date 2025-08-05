from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
from sspi_flask_app.models.database import sspi_metadata 
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
        Raises an InvalidDocumentFormatError if the document is not in valid
        RawDocument format

        Valid Raw Document Format:
            {
                "CollectionInfo": {
                    "Username": str,
                    "Date": str
                }
                "Source": {
                    "OrganizationCode": str,
                    "OrganizationQueryCode": str
                    "QueryCode": str
                },
                "Raw": str or dict or int or float,
                ...
            }
        The fields IndicatorCode, Raw, and CollectedAt are required.
        Additional fields are allowed, but not required.
        """
        self.validate_raw(document, document_number)
        self.validate_collection_info(document, document_number)
        self.validate_source_info(document, document_number)

    def tabulate_ids(self):
        tab_ids = self._mongo_database.aggregate([
            {"$group": {
                "_id": {
                    "Source": "$Source",
                    "Raw": "$Raw"
                },
                "count": {"$sum": 1},
                "ids": {"$push": "$_id"}
            }},
        ])
        return json.loads(json_util.dumps(tab_ids))

    def validate_collection_info(self, document: dict, document_number: int = 0):
        # Validate Date format
        if "CollectionInfo" not in document.keys():
            print(f"Document Produced an Error: {document}")
            doc_id = f"(document {document_number})"
            raise InvalidDocumentFormatError(
                f"'CollectionInfo' is a required field {doc_id}")
        if "Date" not in document["CollectionInfo"].keys():
            print(f"Document Produced an Error: {document}")
            doc_id = f"(document {document_number})"
            raise InvalidDocumentFormatError(
                f"'Date' is a required field of CollectionInfo {doc_id}")
        if not isinstance(document["CollectionInfo"]["Date"], str):
            print(f"Document Produced an Error: {document}")
            doc_id = f"(document {document_number})"
            raise InvalidDocumentFormatError(
                f"'Date' must be a str {(doc_id)}")
        if "Username" not in document["CollectionInfo"].keys():
            print(f"Document Produced an Error: {document}")
            doc_id = f"(document {document_number})"
            raise InvalidDocumentFormatError(
                f"'Username' is a required field of CollectionInfo  {doc_id}")
        if not isinstance(document["CollectionInfo"]["Username"], str):
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Username' must be a str (document {document_number})")

    def validate_source_info(self, document: dict, document_number: int = 0):
        # Validate Source format
        if "Source" not in document.keys():
            print(f"Document Produced an Error: {document}")
            doc_id = f"(document {document_number})"
            raise InvalidDocumentFormatError(
                f"'Source' is a required field {doc_id}")
        if not isinstance(document["Source"], dict):
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Source' must be a dict (document {document_number})")
        if not all([isinstance(k, str) for k in document["Source"].keys()]):
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"All Source keys must be strings (document {document_number})")
        if not all([isinstance(v, str) for v in document["Source"].values()]):
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"All Source Values must be strings (document {document_number})")
        if "OrganizationCode" not in document["Source"].keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"Source dict must contain an OrganizationCode (document {document_number})")
        if "QueryCode" not in document["Source"].keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"Source dict must contain an QueryCode (document {document_number})")

    def validate_raw(self, document: dict, document_number: int = 0):
        # Validate Raw format
        if "Raw" not in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Raw' is a required argument (document {document_number})")
        if type(document["Raw"]) not in [str, dict, int, float, list]:
            print(f"Document Produced an Error: {type(document["Raw"])}")
            # print(f"Document Produced an Error: {document}")
            doc_id = f"(document {document_number})"
            raise InvalidDocumentFormatError(
                f"'Raw' must be a string, dict, int, float, or list {doc_id}")

    def raw_insert_one(self, document: list | str | dict, source_info: dict[str, str], **kwargs) -> int:
        """
        Utility Function the response from an API call in the database
        - Document to be passed as a well-formed dictionary or string for entry
        into pymongo
        - Implements automatic fragmentation to handle strings which are too large
        :param source_id: Dictionary uniquely identifying raw document sets
        """
        username = kwargs.get("username", None)
        assert username is not None, "username must be provided as a key word argument to raw_insert_one"
        obs = {
            "CollectionInfo": {
                "Date": datetime.now().strftime("%F %R"),
                "Username": username,
            },
            "Source": source_info
        }
        byte_max = self.maximum_document_size_bytes
        if isinstance(document, str) and len(document) > byte_max:
            print(f"Document too large, fragmenting: {len(document)} bytes")
            num_fragments = (len(document) + byte_max - 1) // byte_max
            source_info_id = f"{source_info['OrganizationCode']}_{source_info['QueryCode']}"
            fragment_group_id = hashlib.blake2b(document.encode('utf-8')).hexdigest()
            for i in range(num_fragments):
                obs["Raw"] = document[byte_max * i:byte_max * i + byte_max]
                obs.update(kwargs)
                obs.update({
                    "FragmentGroupID": f"{source_info_id}_{fragment_group_id}",
                    "FragmentNumber": i,
                    "FragmentTotal": num_fragments,
                })
                self.insert_one(obs)
                del obs["_id"]
            return num_fragments
        obs["Raw"] = document
        obs.update(kwargs)
        self.insert_one(obs)
        return 1

    def raw_insert_many(self, document_list: list,  source_info: dict[str, str], **kwargs) -> int:
        """
        Utility Function
        - Observation to be past as a list of well form observation
        dictionaries
        - raw_document_set_id specifies the RawDocumentSet to which the RawDocument belongs
        """
        for observation in document_list:
            self.raw_insert_one(observation, source_info, **kwargs)
        return len(document_list)

    def fetch_raw_data(self, source_info: dict[str, str], **kwargs) -> list:
        """
        Utility function that handles querying the database.

        Kwargs passed to this function are used to update the pymongo query
        """
        source_query = self.build_source_query(source_info)
        raw_data = self.find(source_query, **kwargs)
        if not raw_data:
            raise ValueError(
                "No Documents found with provided source_info in "
                "sspi_raw_api_data. Try running collect!"
            )
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
            assert all([isinstance(x["Raw"], str) for x in v]), "All fragments must have a Raw field of type str"
            raw = "".join([x["Raw"] for x in v])
            drops = ["FragmentNumber", "FragmentTotal", "Raw"]
            rebuilt = {f: data for f, data in v[0].items() if f not in drops}
            rebuilt["Raw"] = raw
            defragged_raw.append(rebuilt)
        return defragged_raw

    def raw_data_available(self, source_info) -> bool:
        """
        Check if raw data is available for a given source.
        :param source_info: Dictionary containing the source information
        :return: True if raw data is available, False otherwise
        """
        source_query = self.build_source_query(source_info)
        return self.find_one(source_query) is not None

    def build_source_query(self, source_info: dict[str, str]) -> dict:
        """
        Given a source_info dictionary, build a query to find documents 
        with matching source information.
        :param source_info: Dictionary containing source information
        :return: A dictionary representing the query to be used in MongoDB
        """
        source_query = {}
        for k,v in source_info.items():
            source_query["Source." + k] = v
        return source_query

    def get_collection_info(self, source_info: dict[str, str]) -> dict:
        """
        Get the collection information for a given source.
        :param source_info: Dictionary containing the source information
        :return: A dictionary containing the collection information
        """
        source_query = self.build_source_query(source_info)
        doc = self.find_one(source_query, {"CollectionInfo": 1})
        if not doc:
            return {}
        return doc["CollectionInfo"]
