from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
from sspi_flask_app.models.errors import InvalidDocumentFormatError
from flask import current_app as app
import os
import re
import json
from bson import json_util
import pandas as pd
import logging

log = logging.getLogger(__name__)


class SSPIMetadata(MongoWrapper):
    def __init__(self, mongo_database, indicator_detail_file=None, intermediate_detail_file=None):
        super().__init__(mongo_database)
        if indicator_detail_file is None:
            indicator_detail_file = "IndicatorDetails.csv"
        if intermediate_detail_file is None:
            intermediate_detail_file = "IntermediateDetails.csv"
        self.indicator_detail_file = indicator_detail_file
        self.intermediate_detail_file = intermediate_detail_file

    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Raises an InvalidDocumentFormatError if the document is not in the
        valid document format

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
        if "DocumentType" not in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'DocumentType' is required (document {document_number})"
            )
        if not type(document["DocumentType"]) is str:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'DocumentType' must be a string (document {document_number})"
            )

    def validate_metadata(self, document: dict, document_number: int = 0):
        # Validate Metadata format
        if "Metadata" not in document.keys():
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Metadata' is a required arg (document {document_number})"
            )
        if not type(document["Metadata"]) in [str, dict, int, float, list]:
            print(f"Document Produced an Error: {document}")
            raise InvalidDocumentFormatError(
                f"'Metadata' must be a string, dict, int, float, or list (document {
                    document_number})"
            )

    def load(self) -> int:
        """
        Loads the metadata into the database
        """
        local_path = os.path.join(os.path.dirname(app.instance_path), "local")
        full_path = os.path.join(local_path, self.indicator_detail_file)
        log.debug(f"Loading data for {self.name} from file {full_path}")
        print(f"Loading data for {self.name} from file {full_path}")
        indicator_details = pd.read_csv(full_path)
        intermediate_details = pd.read_csv(
            os.path.join(local_path, self.intermediate_detail_file))
        with open(os.path.join(local_path, "CountryGroups.json")) as file:
            country_groups = json.load(file)
        metadata = self.build_metadata(
            indicator_details,
            intermediate_details,
            country_groups
        )
        count = self.insert_many(metadata)
        self.drop_duplicates()
        log.info(f"Successfully loaded {count} documents into {self.name}")
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
        json_string = str(intermediate_details.to_json(orient="records"))
        intermediate_details_list = json.loads(json_string)
        return [
            {"DocumentType": "IntermediateDetail", "Metadata": intermediate_detail}
            for intermediate_detail in intermediate_details_list
        ]

    def build_indicator_details(self, indicator_details: pd.DataFrame, intermediate_details: pd.DataFrame):
        json_string = str(indicator_details.to_json(orient="records"))
        indicator_details_list = json.loads(json_string)
        ind_int_map = {}
        for intermediate_detail in intermediate_details.to_dict(orient="records"):
            if intermediate_detail["IndicatorCode"] not in ind_int_map.keys():
                ind_int_map[intermediate_detail["IndicatorCode"]] = []
            ind_int_map[intermediate_detail["IndicatorCode"]].append(intermediate_detail)
        print(ind_int_map)
        for indicator_detail in indicator_details_list:
            indicator_detail["DocumentType"] = "IndicatorDetail"
            if indicator_detail["IndicatorCode"] not in ind_int_map.keys():
                continue
            intermediate_codes = [
                x["IntermediateCode"] for x in ind_int_map[indicator_detail["IndicatorCode"]]
            ]
            indicator_detail["IntermediateCodes"] = intermediate_codes
        return [
            {"DocumentType": "IndicatorDetail", "Metadata": indicator_detail}
            for indicator_detail in indicator_details_list
        ]

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

    def country_group(self, CountryGroupName: str) -> list[str]:
        """
        Return a list of all countries in the country group
        """
        return self.find_one({
            "DocumentType": "CountryGroup",
            "Metadata.CountryGroupName": {
                "$regex": f"^{CountryGroupName}$",
                "$options": "i"}
        })["Metadata"]["Countries"]

    def country_groups(self) -> list[str]:
        """
        Return a list of all country groups in the database
        """
        return self.find_one({"DocumentType": "CountryGroups"})["Metadata"]

    def country_groups_tree(self) -> list[str]:
        """
        Return a list of all country groups in the database
        """
        groups_tree = []
        for g in self.find({"DocumentType": "CountryGroup"}):
            groups_tree.append({
                g["Metadata"]["CountryGroupName"]: g["Metadata"]["Countries"]
            })
        return groups_tree

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
        Return a list of metadata dictionaries containing indicator details
        """
        flat_list = []
        for detail in self.find({"DocumentType": "IndicatorDetail"}):
            flat_list.append(detail["Metadata"])
        return flat_list

    def get_indicator_detail(self, IndicatorCode: str) -> dict:
        """
        Return the detail for a particular indicator for IndicatorCode
        """
        query = {
            "DocumentType": "IndicatorDetail",
            "Metadata.IndicatorCode": IndicatorCode
        }
        return self.find_one(query)["Metadata"]

    def get_goalposts(self, IndicatorCode: str):
        """
        Return a list of documents containg indicator details
        """
        indicator_detail = self.get_indicator_detail(IndicatorCode)
        lg = indicator_detail["LowerGoalpost"]
        ug = indicator_detail["UpperGoalpost"]
        return lg, ug

    def intermediate_details(self) -> list[dict]:
        """
        Return a list of documents containg intermediate details
        """
        flat_list = []
        for detail in self.find({"DocumentType": "IntermediateDetail"}):
            flat_list.append(detail["Metadata"])
        return flat_list

    def intermediate_codes(self) -> list[str]:
        """
        Return a list of documents containg intermediate details
        """
        code_list = []
        for detail in self.find({"DocumentType": "IntermediateDetail"}):
            code_list.append(detail["Metadata"]["IntermediateCode"])
        return code_list

    def get_intermediate_detail(self, IntermediateCode: str) -> dict:
        """
        Return a document containing indicator details for a specific IndicatorCode
        """
        query = {
            "DocumentType": "IntermediateDetail",
            "Metadata.IntermediateCode": IntermediateCode
        }
        return self.find_one(query)["Metadata"]
