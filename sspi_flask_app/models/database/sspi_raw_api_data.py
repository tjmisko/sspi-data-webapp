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
                    "OrganizationSeriesCode": str
                },
                "Raw": str or dict or int or float,
                ...
            }
        The fields IndicatorCode, Raw, and CollectedAt are required.
        Additional fields are allowed, but not required.
        """
        self.validate_raw(document, document_number)
        self.validate_collection_info(document, document_number)

    def tabulate_ids(self):
        tab_ids = self._mongo_database.aggregate([
            {"$group": {
                "_id": {
                    "RawDocumentSetID": "$RawDocumentSetID",
                    "Raw": "$Raw"
                },
                "count": {"$sum": 1},
                "ids": {"$push": "$_id"}
            }},
        ])
        return json.loads(json_util.dumps(tab_ids))

    def validate_collection_info(self, document: dict, document_number: int = 0):
        # Validate Date format
        if "CollectionInfo" not in document["CollectionInfo"].keys():
            print(f"Document Produced an Error: {document}")
            doc_id = f"(document {document_number})"
            raise InvalidDocumentFormatError(
                f"'Date' is a required argument {doc_id}")
        if "Date" not in document["CollectionInfo"].keys():
            print(f"Document Produced an Error: {document}")
            doc_id = f"(document {document_number})"
            raise InvalidDocumentFormatError(
                f"'Date' is a required argument {doc_id}")
        if not isinstance(document["CollectionInfo"]["Date"], str):
            print(f"Document Produced an Error: {document}")
            doc_id = f"(document {document_number})"
            raise InvalidDocumentFormatError(
                f"'Date' must be a str {(doc_id)}")
        if "Username" not in document["CollectionInfo"].keys():
            print(f"Document Produced an Error: {document}")
            doc_id = f"(document {document_number})"
            raise InvalidDocumentFormatError(
                f"'Username' is a required argument {doc_id}")
        if not isinstance(document["CollectionInfo"]["Username"], str):
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Username' must be a str (document {document_number})")

    def validate_source(self, document: dict, document_number: int = 0):
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
        if not "OraganizationCode" in document["Source"].keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"Source dict must contain an OrganizationCode (document {document_number})")
        if not "OrganizationSeriesCode" in document["Source"].keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"Source dict must contain an OrganizationSeriesCode (document {document_number})")

    def validate_raw(self, document: dict, document_number: int = 0):
        # Validate Raw format
        if "Raw" not in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Raw' is a required argument (document {document_number})")
        if type(document["Raw"]) not in [str, dict, int, float, list]:
            print(f"Document Produced an Error: {document}")
            doc_id = f"(document {document_number})"
            raise InvalidDocumentFormatError(
                f"'Raw' must be a string, dict, int, float, or list {doc_id}")

    def raw_insert_one(self, document: list | str | dict, source_id: dict[str, str], **kwargs) -> int:
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
            "Source": source_id
        }
        byte_max = self.maximum_document_size_bytes
        if isinstance(document, str) and len(document) > byte_max:
            num_fragments = (len(document) + byte_max - 1) // byte_max
            fragment_group_id = hashlib.blake2b(document.encode('utf-8')).hexdigest()
            for i in range(num_fragments):
                obs["Raw"] = document[byte_max * i:byte_max * i + byte_max],
                obs.update(kwargs)
                obs.update({
                    "FragmentGroupID": f"{raw_document_set_id}_{fragment_group_id}",
                    "FragmentNumber": i,
                    "FragmentTotal": num_fragments,
                })
                self.insert_one(obs)
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

    def fetch_raw_data(self, raw_document_set_id, **kwargs) -> list:
        """
        Utility function that handles querying the database.

        Kwargs passed to this function are used to update the pymongo query
        """
        if not bool(self.find_one({"RawDocumentSetID": raw_document_set_id})):
            raise ValueError(
                "No Documents with RawDocumentSetID " f"{raw_document_set_id} in "
                "sspi_raw_api_data. Do you forget to run collect?"
            )
        mongoQuery = {"RawDocumentSetID": raw_document_set_id}
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

    def raw_data_available(self, raw_document_set_id, **kwargs) -> bool:
        """
        Returns True if raw data is available for the given indicator code and
        kwargs
        """
        mongo_query = {"RawDocumentSetID": raw_document_set_id}
        mongo_query.update(kwargs)
        return bool(self.find_one(mongo_query))

    def get_collection_info(self, series_code):


    def get_source_info(self, series_code):


    def check_coverage(self, dataset_list) -> tuple[list[str], list[str]]:
        """
        Checks the coverage of the raw API data for the given dataset list.
        Returns a tuple of uncollected datasets and collected datasets.
        """
        uncollected_datasets = []
        collected_datasets = []
        for ds_code in dataset_list:
            source_info = sspi_metadata.get_source_info(ds_code)
            # check whether that source has been collected 
        return uncollected_datasets, collected_datasets

