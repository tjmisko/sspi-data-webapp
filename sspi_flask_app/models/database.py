import re
import os
import json
from flask import current_app as app
import pandas as pd
from datetime import datetime
from bson import ObjectId, json_util
from .errors import InvalidDocumentFormatError


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
        if not "Unit" in document.keys():
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


class SSPIPartialAPIData(MongoWrapper):

    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        """
        self.validate_country_code(document, document_number)
        self.validate_indicator_code(document, document_number)
        self.validate_year(document, document_number)
        self.validate_intermediates(document, document_number)


class SSPIRawAPIData(MongoWrapper):
    def validate_document_format(self, document: dict, document_number: int = 0):
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
        if not "CollectedAt" in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'CollectedAt' is a required argument (document {document_number})")
        if not type(document["CollectedAt"]) is datetime:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'CollectedAt' must be a datetime (document {document_number})")

    def validate_username(self, document: dict, document_number: int = 0):
        # Validate Username format
        if not "Username" in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Username' is a required argument (document {document_number})")
        if not type(document["Username"]) is str:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Username' must be a str (document {document_number})")

    def validate_raw(self, document: dict, document_number: int = 0):
        # Validate Raw format
        if not "Raw" in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Raw' is a required argument (document {document_number})")
        if not type(document["Raw"]) in [str, dict, int, float, list]:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Raw' must be a string, dict, int, float, or list (document {document_number})")

    def raw_insert_one(self, document, IndicatorCode, **kwargs) -> int:
        """
        Utility Function the response from an API call in the database
        - Observation to be passed as a well-formed dictionary for entry into pymongo
        - IndicatorCode is the indicator code for the indicator that the observation is for
        """
        document = {
            "IndicatorCode": IndicatorCode,
            "Raw": document,
            "CollectedAt": datetime.now()
        }
        document.update(kwargs)
        self.insert_one(document)
        return 1

    def raw_insert_many(self, document_list, IndicatorCode, **kwargs) -> int:
        """
        Utility Function 
        - Observation to be past as a list of well form observation dictionaries
        - IndicatorCode is the indicator code for the indicator that the observation is for
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
        Returns True if raw data is available for the given indicator code and kwargs
        """
        MongoQuery = {"IndicatorCode": IndicatorCode}
        MongoQuery.update(kwargs)
        return bool(self.find_one(MongoQuery))


class SSPIMainDataV3(MongoWrapper):

    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Raises an InvalidDocumentFormatError if the document is not in the valid

        Valid Document Format:
            {
                "IndicatorCode": str,
                "CountryCode": str,
                "Raw": float or int
                "Year": int,
                "Value": float,
                "Score": float,
            }
        Additional fields are allowed but not required
        """
        self.validate_country_code(document, document_number)
        self.validate_indicator_code(document, document_number)
        self.validate_year(document, document_number)
        self.validate_value(document, document_number)

    def load(self) -> int:
        """
        Loads the metadata into the database
        """
        local_path = os.path.join(os.path.dirname(app.instance_path), "local")
        sspi_main_data_wide = pd.read_csv(os.path.join(
            local_path, "SSPIMainDataV3.csv"), skiprows=1)
        sspi_main_data_documents = self.process_sspi_main_data(
            sspi_main_data_wide)
        count = self.insert_many(sspi_main_data_documents)
        self.drop_duplicates()
        print(f"Successfully loaded {count} documents into {self.name}")
        return count

    def process_sspi_main_data(self, sspi_main_data_wide: pd.DataFrame) -> list[dict]:
        """
        Utility function that builds the metadata JSON list from the IndicatorDetails.csv and IntermediateDetails.csv files
        """
        sspi_main_data_long = pd.melt(sspi_main_data_wide, id_vars=[
                                      "Country Code", "Country"], var_name="Variable", value_name="Value")
        sspi_main_data_long = sspi_main_data_long.rename(
            columns={"Country Code": "CountryCode"})
        sspi_main_data_long["IndicatorCode"] = sspi_main_data_long["Variable"].str.extract(
            r"([A-Z0-9]{6})_[A-Z]+")
        sspi_main_data_long["VariableType"] = sspi_main_data_long["Variable"].str.extract(
            r"[A-Z0-9]{6}_([A-Z]+)")
        sspi_main_data_long.dropna(subset=["IndicatorCode"], inplace=True)
        sspi_main_data_long["VariableType"] = sspi_main_data_long["VariableType"].map(
            lambda s: s.title())
        sspi_main_data_documents = sspi_main_data_long.pivot(
            index=["CountryCode", "IndicatorCode"], columns="VariableType", values="Value").reset_index()
        sspi_main_data_documents["Year"] = sspi_main_data_documents["Year"].astype(str).map(
            lambda s: re.match(r"[0-9]{4}", s)).map(lambda m: m.group(0) if m else "0").astype(int)
        sspi_main_data_documents = sspi_main_data_documents[sspi_main_data_documents.Year > 0]
        sspi_main_data_documents["Value"] = sspi_main_data_documents["Raw"].astype(
            float)
        sspi_main_data_documents["Score"] = sspi_main_data_documents["Score"].astype(
            float)
        sspi_main_data_documents.drop(columns=["Raw"], inplace=True)
        document_list = json.loads(
            str(sspi_main_data_documents.to_json(orient="records")))
        return document_list


class SSPIMetadata(MongoWrapper):

    def validate_document_format(self, document: dict, document_number: int = 0):
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

    def tabulate_ids(self):
        tab_ids = self._mongo_database.aggregate([
            {"$group": {
                "_id": {
                    "DocumentType": "$DocumentType",
                    "Metadata": "$Metadata"
                },
                "count": {"$sum": 1},
                "ids": {"$push": "$_id"}
            }},
        ])
        return json.loads(json_util.dumps(tab_ids))

    def validate_document_type(self, document: dict, document_number: int = 0):
        # Validate DocumentType format
        if not "DocumentType" in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'DocumentType' is a required argument (document {document_number})")
        if not type(document["DocumentType"]) is str:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'DocumentType' must be a string (document {document_number})")

    def validate_metadata(self, document: dict, document_number: int = 0):
        # Validate Metadata format
        if not "Metadata" in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Metadata' is a required argument (document {document_number})")
        if not type(document["Metadata"]) in [str, dict, int, float, list]:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Metadata' must be a string, dict, int, float, or list (document {document_number})")

    def load(self) -> int:
        """
        Loads the metadata into the database
        """
        local_path = os.path.join(os.path.dirname(app.instance_path), "local")
        indicator_details = pd.read_csv(
            os.path.join(local_path, "IndicatorDetails.csv"))
        intermediate_details = pd.read_csv(
            os.path.join(local_path, "IntermediateDetails.csv"))
        with open(os.path.join(local_path, "CountryGroups.json")) as file:
            country_groups = json.load(file)
        metadata = self.build_metadata(
            indicator_details,
            intermediate_details,
            country_groups
        )
        count = self.insert_many(metadata)
        self.drop_duplicates()
        print(f"Successfully loaded {count} documents into {self.name}")
        return count

    def build_metadata(self, indicator_details: pd.DataFrame, intermediate_details: pd.DataFrame, country_groups: dict) -> list:
        """
        Utility function that builds the metadata JSON list from the IndicatorDetails.csv and IntermediateDetails.csv files
        """
        metadata = []
        metadata.append(self.build_pillar_codes(indicator_details))
        metadata.append(self.build_category_codes(indicator_details))
        metadata.append(self.build_indicator_codes(indicator_details))
        metadata.append(self.build_intermediate_codes(intermediate_details))
        metadata.extend(self.build_country_groups(country_groups))
        metadata.extend(self.build_intermediate_details(intermediate_details))
        metadata.extend(self.build_indicator_details(
            indicator_details, intermediate_details))
        return metadata

    def build_pillar_codes(self, indicator_details: pd.DataFrame) -> dict:
        pillar_codes = indicator_details["PillarCode"].unique().tolist()
        return {"DocumentType": "PillarCodes", "Metadata": pillar_codes}

    def build_category_codes(self, indicator_details: pd.DataFrame) -> dict:
        category_codes = indicator_details["CategoryCode"].unique().tolist()
        return {"DocumentType": "CategoryCodes", "Metadata": category_codes}

    def build_indicator_codes(self, indicator_details: pd.DataFrame) -> dict:
        indicator_codes = indicator_details["IndicatorCode"].unique().tolist()
        return {"DocumentType": "IndicatorCodes", "Metadata": indicator_codes}

    def build_intermediate_codes(self, intermediate_details: pd.DataFrame) -> dict:
        intermediate_codes = intermediate_details["IntermediateCode"].unique(
        ).tolist()
        return {"DocumentType": "IntermediateCodes", "Metadata": intermediate_codes}

    def build_country_groups(self, country_groups: dict) -> list[dict]:
        country_groups_lookup = [{
            "DocumentType": "CountryGroups",
            "Metadata": list(country_groups.keys())
        }]
        country_group_list = []
        for group_name, codelist in country_groups.items():
            country_group_list.append({
                "DocumentType": "CountryGroup",
                "Metadata": {
                    "CountryGroupName": group_name,
                    "Countries": codelist
                }
            })
        return country_groups_lookup + country_group_list

    def build_intermediate_details(self, intermediate_details: pd.DataFrame) -> list[dict]:
        intermediate_details_list = json.loads(
            str(intermediate_details.to_json(orient="records")))
        return [{"DocumentType": "IntermediateDetail", "Metadata": intermediate_detail} for intermediate_detail in intermediate_details_list]

    def build_indicator_details(self, indicator_details: pd.DataFrame, intermediate_details: pd.DataFrame):
        json_string = str(indicator_details.to_json(orient="records"))
        indicator_details_list = json.loads(json_string)
        for indicator_detail in indicator_details_list:
            indicator_detail["DocumentType"] = "IndicatorDetail"
            # Link intermediate_details to their corresponding indicator_detail
            if indicator_detail["IntermediateCodes"] is not None:
                intermediate_codes = re.findall(
                    r"[A-Z0-9]{6}", indicator_detail["IntermediateCodes"])
                indicator_detail["IntermediateCodes"] = intermediate_codes
                filtered_intermediate_details = intermediate_details.loc[
                    intermediate_details["IndicatorCode"] == indicator_detail["IndicatorCode"]]
                filtered_intermediate_details_list = json.loads(
                    str(filtered_intermediate_details.to_json(orient="records")))
                indicator_detail["IntermediateDetails"] = filtered_intermediate_details_list
        return [{"DocumentType": "IndicatorDetail", "Metadata": indicator_detail} for indicator_detail in indicator_details_list]

    # Getters
    def pillar_codes(self) -> list[str]:
        """
        Return a list of all pillar codes
        """
        return self.find_one({"DocumentType": "PillarCodes"})["Metadata"]

    def category_codes(self) -> list[str]:
        """
        Return a list of all category codes
        """
        return self.find_one({"DocumentType": "CategoryCodes"})["Metadata"]

    def indicator_codes(self) -> list[str]:
        """
        Return a list of all indicator codes
        """
        return self.find_one({"DocumentType": "IndicatorCodes"})["Metadata"]

    def country_groups(self) -> list[str]:
        """
        Return a list of all country groups in the database
        """
        return self.find_one({"DocumentType": "CountryGroups"})["Metadata"]

    def get_country_groups(self, CountryCode: str) -> list[str]:
        """
        Return a list containing the group names to which the country belongs
        """
        groups = self.find({"DocumentType": "CountryGroup"})
        group_list = []
        for g in groups:
            if CountryCode in g["Metadata"]["Countries"]:
                group_list.append(g["Metadata"]["CountryGroupName"])
        return group_list

    def indicator_details(self) -> list[dict]:
        """
        Return a list of documents containg indicator details
        """
        return self.find({"DocumentType": "IndicatorDetail"})

    def get_detail(self, IndicatorCode: str) -> dict:
        """
        Return a list of documents containg indicator details
        """
        query = {
            "DocumentType": "IndicatorDetail",
            "Metadata.IndicatorCode": IndicatorCode
        }
        return self.find_one(query)

    def intermediate_details(self) -> list[dict]:
        """
        Return a list of documents containg intermediate details
        """
        return self.find({"DocumentType": "IntermediateDetail"})


class SSPIProductionData(MongoWrapper):

    def __init__(self, mongo_database):
        self._mongo_database = mongo_database
        self._mongo_database.create_index(
            [("CCode", 1), ("ICode", 1), ("Year", 1)])
        self.name = mongo_database.name

    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Raises an InvalidDocumentFormatError if the document is not in the valid

        Valid Document Format:
            {
                "Endpoint": str,
                ...
            }
        Additional fields are allowed but not required
        """
        pass
