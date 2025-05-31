from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
from sspi_flask_app.models.errors import InvalidDocumentFormatError
from flask import current_app as app
import os
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
        if type(document["DocumentType"]) is not str:
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
        if type(document["Metadata"]) not in [str, dict, int, float, list]:
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
        ind_detail_path = os.path.join(local_path, self.indicator_detail_file)
        print(f"Loading data for {self.name} from file {ind_detail_path}")
        indicator_details = pd.read_csv(ind_detail_path)
        int_detail_path = os.path.join(
            local_path, self.intermediate_detail_file
        )
        print(f"Loading data for {self.name} from file {int_detail_path}")
        intermediate_details = pd.read_csv(int_detail_path)
        with open(os.path.join(local_path, "CountryGroups.json")) as file:
            country_groups = json.load(file)
        with open(os.path.join(local_path, "country-flag-colors.json")) as file:
            country_colors = json.load(file)
        with open(os.path.join(local_path, "sspi-colors.json")) as file:
            sspi_custom_colors = json.load(file)
        metadata = self.build_metadata(
            indicator_details,
            intermediate_details,
            country_groups,
            country_colors,
            sspi_custom_colors
        )
        count = self.insert_many(metadata)
        self.drop_duplicates()
        print(f"Successfully loaded {count} documents into {self.name}")
        return count

    def build_metadata(self, indicator_details: pd.DataFrame, intermediate_details: pd.DataFrame, country_groups: dict, country_colors: list[dict], sspi_custom_colors: dict) -> list:
        """
        Utility function that builds the metadata JSON list from the IndicatorDetails.csv and IntermediateDetails.csv files
        """
        metadata = []
        metadata.append(self.build_pillar_codes(indicator_details))
        metadata.append(self.build_category_codes(indicator_details))
        metadata.append(self.build_indicator_codes(indicator_details))
        metadata.append(self.build_intermediate_codes(intermediate_details))
        metadata.extend(self.build_country_groups(country_groups))
        metadata.extend(self.build_country_details(country_groups, country_colors, sspi_custom_colors))
        metadata.extend(self.build_intermediate_details(intermediate_details))
        metadata.extend(self.build_indicator_details(indicator_details, intermediate_details))
        metadata.extend(self.build_category_details(indicator_details))
        metadata.extend(self.build_pillar_details(indicator_details))
        metadata.extend(self.build_overall_detail(indicator_details))
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

    def build_country_details(self, country_groups: dict, country_colors: list[dict], sspi_custom_colors: dict) -> list[dict]:
        """
        Builds a list of country details from the country groups and colors
        """
        details = []
        for cou in country_colors:
            if "CountryCode" not in cou.keys():
                continue
            details.append({
                "DocumentType": "CountryDetail",
                "Metadata": cou
            })
            if cou["CountryCode"] in sspi_custom_colors.keys():
                cou["SSPIColor"] = sspi_custom_colors[cou["CountryCode"]]
        return details


        
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
            ind_int_map[intermediate_detail["IndicatorCode"]].append(
                intermediate_detail)
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

    def build_category_details(self, indicator_details: pd.DataFrame) -> list[dict]:
        json_string = str(indicator_details.to_json(orient="records"))
        indicator_details_list = json.loads(json_string)
        category_detail_map = {}
        for indicator in indicator_details_list:
            if indicator["CategoryCode"] not in category_detail_map.keys():
                category_detail_map[indicator["CategoryCode"]] = {
                    "CategoryCode": indicator["CategoryCode"],
                    "Category": indicator["Category"],
                    "PillarCode": indicator["PillarCode"],
                    "Pillar": indicator["Pillar"],
                    "IndicatorCodes": []
                }
            category_detail_map[indicator["CategoryCode"]]["IndicatorCodes"].append(
                indicator["IndicatorCode"]
            )
        return [
            {"DocumentType": "CategoryDetail", "Metadata": category_detail} for
            category_detail in category_detail_map.values()
        ]

    def build_pillar_details(self, indicator_details: pd.DataFrame) -> list[dict]:
        json_string = str(indicator_details.to_json(orient="records"))
        indicator_details_list = json.loads(json_string)
        pillar_detail_map = {}
        for indicator in indicator_details_list:
            if indicator["PillarCode"] not in pillar_detail_map.keys():
                pillar_detail_map[indicator["PillarCode"]] = {
                    "PillarCode": indicator["PillarCode"],
                    "Pillar": indicator["Pillar"],
                    "CategoryCodes": set(),
                    "IndicatorCodes": []
                }
            pillar_detail_map[indicator["PillarCode"]]["CategoryCodes"].add(
                indicator["CategoryCode"]
            )
            pillar_detail_map[indicator["PillarCode"]]["IndicatorCodes"].append(
                indicator["IndicatorCode"]
            )
        for pillar_code in pillar_detail_map.keys():
            pillar_detail_map[pillar_code]["CategoryCodes"] = list(
                pillar_detail_map[pillar_code]["CategoryCodes"]
            )
        return [
            {"DocumentType": "PillarDetail", "Metadata": pillar_detail} for
            pillar_detail in pillar_detail_map.values()
        ]

    def build_overall_detail(self, indicator_details: pd.DataFrame) -> list[dict]:
        json_string = str(indicator_details.to_json(orient="records"))
        indicator_details_list = json.loads(json_string)
        overall_detail = {
            "Code": "SSPI",
            "Name": "Sustainable and Shared Prosperity Policy Index",
            "PillarCodes": set(),
            "CategoryCodes": set(),
            "IndicatorCodes": []
        }
        for indicator in indicator_details_list:
            overall_detail["PillarCodes"].add(indicator["PillarCode"])
            overall_detail["CategoryCodes"].add(indicator["CategoryCode"])
            overall_detail["IndicatorCodes"].append(indicator["IndicatorCode"])
        overall_detail["PillarCodes"] = list(overall_detail["PillarCodes"])
        overall_detail["CategoryCodes"] = list(overall_detail["CategoryCodes"])
        return [
            {"DocumentType": "OverallDetail", "Metadata": overall_detail}
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

    def indicator_options(self) -> list[str]:
        """
        Return a list of documents to build indicator options HTML for the dropdown
        """
        option_list = []
        for detail in self.find({"DocumentType": "IndicatorDetail"}):
            option_list.append({
                "Name": detail["Metadata"]["Indicator"],
                "Code": detail["Metadata"]["IndicatorCode"],
            })
        return option_list

    def category_options(self) -> list[str]:
        """
        Return a list of documents to build category options HTML for the dropdown
        """
        option_list = []
        for detail in self.find({"DocumentType": "CategoryDetail"}):
            option_list.append({
                "Name": detail["Metadata"]["Category"],
                "Code": detail["Metadata"]["CategoryCode"],
            })
        return option_list

    def pillar_options(self) -> list[str]:
        """
        Return a list of documents to build pillar options HTML for the dropdown
        """
        option_list = []
        for detail in self.find({"DocumentType": "PillarDetail"}):
            option_list.append({
                "Name": detail["Metadata"]["Pillar"],
                "Code": detail["Metadata"]["PillarCode"],
            })
        return option_list

    def get_indicator_detail(self, IndicatorCode: str) -> dict:
        """
        Return the detail for a particular indicator for IndicatorCode
        """
        query = {
            "DocumentType": "IndicatorDetail",
            "Metadata.IndicatorCode": IndicatorCode
        }
        return self.find_one(query)["Metadata"]

    def get_goalposts(self, IndicatorCode: str) -> tuple[int | float, int | float]:
        """
        Returns a tuple of the lower and upper goalposts for the given indicator

        :param IndicatorCode: The indicator code for which to get the goalposts
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

    def get_item_detail(self, ItemCode: str) -> dict:
        """
        Return a document containing the item details for a specific ItemCode

        :param ItemCode: The item code for which to get the details (SSPI, PillarCode, CategoryCode, IndicatorCode, IntermediateCode)
        """
        result = self.find_one({
            "$expr": {
                "$eq": [
                    {
                        "$switch": {
                            "branches": [
                                {
                                    "case": {"$eq": ["$DocumentType", "IndicatorDetail"]},
                                    "then": "$Metadata.IndicatorCode"
                                },
                                {
                                    "case": {"$eq": ["$DocumentType", "IntermediateDetail"]},
                                    "then": "$Metadata.IntermediateCode"
                                },
                                {
                                    "case": {"$eq": ["$DocumentType", "CategoryDetail"]},
                                    "then": "$Metadata.CategoryCode"
                                },
                                {
                                    "case": {"$eq": ["$DocumentType", "PillarDetail"]},
                                    "then": "$Metadata.PillarCode"
                                },
                                {
                                    "case": {"$eq": ["$DocumentType", "OverallDetail"]},
                                    "then": "$Metadata.Code"
                                }
                            ],
                            "default": None
                        }
                    },
                    ItemCode
                ]
            }
        })
        if not result:
            return {"Error": "ItemCode not found"}
        result["Metadata"]["DocumentType"] = result["DocumentType"]
        result["Metadata"]["ItemCode"] = ItemCode
        if result["DocumentType"] == "IntermediateDetail":
            result["Metadata"]["ItemName"] = result["Metadata"]["IntermediateName"]
        elif result["DocumentType"] == "IndicatorDetail":
            result["Metadata"]["ItemName"] = result["Metadata"]["Indicator"]
        elif result["DocumentType"] == "CategoryDetail":
            result["Metadata"]["ItemName"] = result["Metadata"]["Category"]
        elif result["DocumentType"] == "PillarDetail":
            result["Metadata"]["ItemName"] = result["Metadata"]["Pillar"]
        elif result["DocumentType"] == "OverallDetail":
            result["Metadata"]["ItemName"] = result["Metadata"]["Name"]
        return result["Metadata"]



    def country_group(self, country_group_name: str) -> list[str]:
        """
        Return a list of all countries in the country group
        """
        if not country_group_name:
            return []
        return self.find_one({
            "DocumentType": "CountryGroup",
            "Metadata.CountryGroupName": {
                "$regex": f"^{country_group_name}$",
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

    def indicator_details(self, filter=[]) -> list[dict]:
        """
        Return a list of metadata dictionaries containing indicator details

        :param filter: A list of indicator codes to filter the results. Only
        details with codes in this list will be returned. If empty, all
        indicator details will be returned.
        """
        flat_list = []
        for detail in self.find({"DocumentType": "IndicatorDetail"}):
            if filter and detail["Metadata"]["IndicatorCode"] not in filter:
                continue
            flat_list.append(detail["Metadata"])
        return flat_list
