from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
import frontmatter
import pycountry
from markdown import markdown
from sspi_flask_app.models.errors import InvalidDocumentFormatError, MethodologyFileError
from flask import current_app as app
import os
import json
import yaml
from bson import json_util
import pandas as pd
import logging

log = logging.getLogger(__name__)


class SSPIMetadataDeprecated(MongoWrapper):
    def __init__(self, mongo_database, indicator_detail_file=None, intermediate_detail_file=None):
        super().__init__(mongo_database)
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
        pass

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
    
    def validate_detail_format(self, detail: dict):
        assert "ItemName" in detail.keys(), "ItemName is required in detail"
        assert "ItemCode" in detail.keys(), "ItemCode is required in detail"
        assert "ItemType" in detail.keys(), "ItemType is required in detail"
        if "LowerGoalpost" in detail.keys() and detail["LowerGoalpost"] is not None:
            assert type(detail["LowerGoalpost"]) in [int, float], "LowerGoalpost must be an int or float"
        if "UpperGoalpost" in detail.keys() and detail["UpperGoalpost"] is not None:
            assert type(detail["UpperGoalpost"]) in [int, float], "UpperGoalpost must be an int or float"
        if detail["ItemType"] not in ["SSPI", "Pillar", "Category", "Indicator", "Intermediate"]:
            raise InvalidDocumentFormatError(
                f"Invalid ItemType {detail['ItemType']} in detail {detail}"
            )
        if detail["ItemType"] == "SSPI":
            assert "PillarCodes" in detail.keys(), "PillarCodes is required for SSPI"
            assert type(detail["PillarCodes"]) is list, "PillarCodes must be a list"
            assert all(isinstance(code, str) for code in detail["PillarCodes"]), "All PillarCodes must be strings"
            pillar_codes = set([p.upper() for p in detail["PillarCodes"]])
            children = set([c.upper() for c in detail["Children"]])
            if pillar_codes != children:
                msg = (
                    f"SSPIFile {detail['ItemCode']} specifies PillarCodes: {pillar_codes}\n"
                    f"Methodology File Tree specifies Children: {children}\n"
                )
                raise MethodologyFileError(msg)
        elif detail["ItemType"] == "Pillar":
            assert "CategoryCodes" in detail.keys(), "CategoryCodes is required for Pillar"
            assert type(detail["CategoryCodes"]) is list, "CategoryCodes must be a list"
            assert all(isinstance(code, str) for code in detail["CategoryCodes"]), "All CategoryCodes must be strings"
            category_codes = set([c.upper() for c in detail["CategoryCodes"]])
            children = set([c.upper() for c in detail["Children"]])
            if category_codes != children:
                msg = (
                    f"PillarFile {detail['ItemCode']} specifies CategoryCodes: {category_codes}\n"
                    f"Methodology File Tree specifies Children: {children}\n"
                )
                raise MethodologyFileError(msg)
        elif detail["ItemType"] == "Category":
            assert "IndicatorCodes" in detail.keys(), "IndicatorCodes is required for Category"
            assert type(detail["IndicatorCodes"]) is list, "IndicatorCodes must be a list"
            assert all(isinstance(code, str) for code in detail["IndicatorCodes"]), "All IndicatorCodes must be strings"
            indicator_codes = set([i.upper() for i in detail["IndicatorCodes"]])
            children = set([c.upper() for c in detail["Children"]])
            if indicator_codes != children:
                msg = (
                    f"CategoryFile {detail['ItemCode']} specifies IndicatorCodes: {indicator_codes}\n"
                    f"Methodology File Tree specifies Children: {children}\n"
                )
                raise MethodologyFileError(msg)
        elif detail["ItemType"] == "Indicator" and detail.get("IntermediateCodes") is not None:
            assert type(detail["IntermediateCodes"]) is list, "IntermediateCodes must be a list"
            assert all(isinstance(code, str) for code in detail["IntermediateCodes"]), "All IntermediateCodes must be strings"
            intermediate_codes = set([i.upper() for i in detail["IntermediateCodes"]])
            children = set([c.upper() for c in detail["Children"]])
            if intermediate_codes != children:
                msg = (
                    f"IndicatorFile {detail['ItemCode']} specifies IntermediateCodes: {intermediate_codes}\n"
                    f"Methodogoly File Tree specifies Children: {children}\n"
                )
                raise MethodologyFileError(msg)


    def load(self) -> int:
        local_path = os.path.join(os.path.dirname(app.instance_path), "local")
        with open(os.path.join(local_path, "country-groups.json")) as file:
            country_groups = json.load(file)
        if self.indicator_detail_file is not None and self.intermediate_detail_file is not None:
            count = self.load_static(
                self.indicator_detail_file,
                self.intermediate_detail_file,
                country_groups
            )
        else:
            count = self.load_dynamic(
                country_groups,
            )
        return count

    def load_dynamic(self, country_groups) -> int:
        """
        Load metadata specified in methodology files into the database

        Canonical order of indicators is specified by the order given in the
        parent list.
        """
        details = self.load_methodology_files()
        for detail in details:
            detail["DocumentType"] = detail["ItemType"] + "Detail"
        item_codes = {
            "SSPI": [],
            "Pillar": [],
            "Category": [],
            "Indicator": [],
            "Intermediate": []
        }
        sorted_details = self.sort_item_details(details)
        pc_sum_tree = self.build_pillar_category_summary_tree(sorted_details)
        for detail in sorted_details:
            item_codes[detail["Metadata"]["ItemType"]].append(detail["Metadata"]["ItemCode"])
        metadata = []
        metadata.extend([
            {"DocumentType": "PillarCodes", "Metadata": item_codes["Pillar"]},
            {"DocumentType": "CategoryCodes", "Metadata": item_codes["Category"]},
            {"DocumentType": "IndicatorCodes", "Metadata": item_codes["Indicator"]},
            {"DocumentType": "IntermediateCodes", "Metadata": item_codes["Intermediate"]}
        ])
        metadata.extend(self.build_country_groups(country_groups))
        metadata.extend(self.build_country_details(country_groups))
        metadata.extend(sorted_details)
        metadata.append(pc_sum_tree)
        count = self.insert_many(metadata)
        self.drop_duplicates()
        print(f"Successfully loaded {count} documents into {self.name}")
        return count

    def sort_item_details(self, details: list[dict]) -> list[dict]:
        """
        Sorts the item details based on the order specified for the appropriate
        children in the methodology files, grouped by ItemType and ItemCode
        """
        def get_intermediate_insert_index(intermediate_code: str, start: int) -> int:
            """
            Returns the index to insert the detail in the sorted list of intermediates
            Necessary because IntermediateCodes are not guaranteed to be unique
            """
            intermediate_index = intermediates_sorted.index(intermediate_code, start)
            insert_index = 1 + len(pillars_sorted) + len(categories_sorted) + len(indicators_sorted) + intermediate_index
            if not sorted_details[insert_index]:
                return insert_index
            return get_intermediate_insert_index(intermediate_code, intermediate_index + 1)

        intermediates = []
        indicators = []
        categories = []
        pillars_sorted = []
        for detail in details:
            if detail["ItemType"] == "SSPI":
                pillars_sorted = detail["PillarCodes"]
                print(pillars_sorted)
            elif detail["ItemType"] == "Pillar":
                categories.append({
                    "PillarCode": detail["ItemCode"],
                    "List": detail["CategoryCodes"]
                })
            elif detail["ItemType"] == "Category":
                indicators.append({
                    "CategoryCode": detail["ItemCode"],
                    "List": detail["IndicatorCodes"]
                })
            elif detail["ItemType"] == "Indicator":
                intermediates.append({
                    "IndicatorCode": detail["ItemCode"],
                    "List": detail.get("IntermediateCodes", [])
                })
        categories.sort(key=lambda x: pillars_sorted.index(x["PillarCode"]))
        categories_sorted = [cat for p_list in categories for cat in p_list["List"]]
        indicators.sort(key=lambda x: categories_sorted.index(x["CategoryCode"]))
        indicators_sorted = [ind for c_list in indicators for ind in c_list["List"]]
        intermediates.sort(key=lambda x: indicators_sorted.index(x["IndicatorCode"]))
        intermediates_sorted = [inter for i_list in intermediates for inter in i_list["List"]]
        n_details = 1 + len(pillars_sorted) + len(categories_sorted) + \
            len(indicators_sorted) + len(intermediates_sorted)
        sorted_details = [dict()] * n_details
        for detail in details: 
            if detail["ItemType"] == "SSPI": #First Element
                insert_index = 0
                detail["ItemOrder"] = 0
            elif detail["ItemType"] == "Pillar": #
                pillar_index = pillars_sorted.index(detail["ItemCode"]) 
                insert_index = 1 + pillar_index
                detail["ItemOrder"] = pillar_index
            elif detail["ItemType"] == "Category":
                category_index = categories_sorted.index(detail["ItemCode"])
                insert_index = 1 + len(pillars_sorted) + category_index
                detail["ItemOrder"] = category_index
            elif detail["ItemType"] == "Indicator":
                indicator_index = indicators_sorted.index(detail["ItemCode"])
                insert_index = 1 + len(pillars_sorted) + len(categories_sorted) + indicator_index
                detail["ItemOrder"] = indicator_index
            elif detail["ItemType"] == "Intermediate":  # Intermediate Codes (e.g. POPULN) are not necessarily unique!
                insert_index = get_intermediate_insert_index(detail["ItemCode"], 0)
            else:
                raise MethodologyFileError(
                    f"Invalid ItemType {detail['ItemType']} in detail {detail}"
                )
            sorted_details[insert_index] = detail
        assert all([isinstance(d, dict) for d in sorted_details]), "All details must be dictionaries"
        expected_details = ["SSPI"] + pillars_sorted + categories_sorted + indicators_sorted + intermediates_sorted
        if any([len(d) == 0 for d in sorted_details]):
            missing_code = expected_details[sorted_details.index({})]
            raise MethodologyFileError(
                f"Expected detail for {missing_code} but found empty dictionary in sorted details"
            )
        packaged_details = []
        for detail in sorted_details:
            packaged_details.append({
                "DocumentType": detail["DocumentType"],
                "Metadata": detail
            })
        return packaged_details
        

    def load_methodology_files(self) -> list:
        """
        Walks through the methodology directory and loads the frontmatter
        of all methodology files
        :return: A list of dictionaries containing the metadata from the methodology files
        """
        method_dir = os.path.join(os.path.dirname(app.instance_path), "methodology")
        details = []
        for dirpath, dirnames, filenames in os.walk(method_dir):
            if not filenames:
                raise MethodologyFileError(
                    f"No methodology.md files found in directory {dirpath}. "
                    "Please ensure that all directories in methodology are appropriately named "
                    "and contain a methodology.md file with YAML Frontmatter defining the "
                    "metadata for the item corresponding to the directory name."
                )
            for methodology_file in filenames:
                if not methodology_file == "methodology.md":
                    raise MethodologyFileError(
                        f"Methodology file {methodology_file} is not named 'methodology.md'. "
                        "Please ensure all methodology files are named 'methodology.md'"
                        "and that they are located in the correct directory."
                    )
                full_methodology_path = os.path.join(dirpath, methodology_file)
                try:
                    detail = frontmatter.load(full_methodology_path)
                except (ValueError, yaml.YAMLError) as e:
                    raise MethodologyFileError(
                        f"Error loading methodology file {full_methodology_path}: {e};\n"
                        "It is likely that there is an error in the YAML frontmatter format."
                    )
                detail = detail.metadata
                if dirpath.endswith("methodology"):
                    tree_path = "sspi"
                else:
                    tree_path = "sspi" + dirpath.split("methodology")[1]
                detail["TreePath"] = tree_path
                detail["Children"] = list([d.upper() for d in dirnames])
                self.validate_detail_format(detail)
                details.append(detail)
        return details

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

    def build_country_details(self, country_groups: dict) -> list[dict]:
        """
        Builds a list of country details from country groups using pycountry
        for country names and flags. Colors are managed on the frontend only.
        """
        # Get unique country codes from all groups
        all_country_codes = set()
        for ccode_list in country_groups.values():
            all_country_codes.update(ccode_list)

        details = []
        for country_code in sorted(all_country_codes):
            # Look up country info from pycountry
            try:
                country = pycountry.countries.get(alpha_3=country_code)
                if not country:
                    log.warning(f"Country code {country_code} not found in pycountry")
                    continue
                country_name = country.name
                flag = country.flag if hasattr(country, 'flag') else ""
            except Exception as e:
                log.warning(f"Error looking up country {country_code}: {e}")
                continue

            # Find which groups this country belongs to
            country_group_list = []
            for group_name, ccode_list in country_groups.items():
                if country_code in ccode_list:
                    country_group_list.append(group_name)

            details.append({
                "DocumentType": "CountryDetail",
                "Metadata": {
                    "Country": country_name,
                    "CountryCode": country_code,
                    "Flag": flag,
                    "CountryGroups": country_group_list
                }
            })
        return details

    def build_pillar_category_summary_tree(self, details) -> dict:
        pc_summary_tree = []
        categories = []
        for detail in details:
            detail = detail["Metadata"]
            if detail["ItemType"] == "Pillar":
                pc_summary_tree.append(detail)
            elif detail["ItemType"] == "Category":
                categories.append(detail)
        pc_summary_tree.sort(key=lambda p: p["ItemOrder"])
        for p in pc_summary_tree:
            p["Categories"] = []
            for c in categories:
                if c["ItemCode"] in p["CategoryCodes"]:
                    p["Categories"].append(c)
            p["Categories"].sort(key=lambda c: c["ItemOrder"])
        return {"DocumentType": "PillarCategorySummaryTree", "Metadata": pc_summary_tree}


    def load_static(self, indicator_detail_file, intermediate_detail_file, country_groups) -> int:
        """
        Loads the metadata from local metadata CSV files into the database
        """
        local_path = os.path.join(os.path.dirname(app.instance_path), "local")
        ind_detail_path = os.path.join(local_path, indicator_detail_file)
        print(f"Loading data for {self.name} from file {ind_detail_path}")
        indicator_details = pd.read_csv(ind_detail_path)
        int_detail_path = os.path.join(
            local_path, intermediate_detail_file
        )
        print(f"Loading data for {self.name} from file {int_detail_path}")
        intermediate_details = pd.read_csv(int_detail_path)
        metadata = []
        metadata.extend(self.build_item_codes_static(indicator_details, intermediate_details))
        metadata.extend(self.build_country_groups(country_groups))
        metadata.extend(self.build_country_details(country_groups))
        metadata.extend(self.build_intermediate_details_static(intermediate_details))
        metadata.extend(self.build_indicator_details_static(indicator_details, intermediate_details))
        metadata.extend(self.build_category_details(indicator_details))
        metadata.extend(self.build_pillar_details_static(indicator_details))
        metadata.extend(self.build_sspi_detail_static(indicator_details))
        count = self.insert_many(metadata)
        self.drop_duplicates()
        print(f"Successfully loaded {count} documents into {self.name}")
        return count

    def build_item_codes_static(self, indicator_details: pd.DataFrame, intermediate_details) -> list[dict]:
        item_codes_metadata = []
        pillar_codes = indicator_details["PillarCode"].unique().tolist()
        item_codes_metadata.append({
            "DocumentType": "PillarCodes",
            "Metadata": pillar_codes
        })
        category_codes = indicator_details["CategoryCode"].unique().tolist()
        item_codes_metadata.append({
            "DocumentType": "CategoryCodes",
            "Metadata": category_codes
        })
        indicator_codes = indicator_details["IndicatorCode"].unique().tolist()
        item_codes_metadata.append({
            "DocumentType": "IndicatorCodes",
            "Metadata": indicator_codes
        })
        intermediate_codes = intermediate_details["IntermediateCode"].unique().tolist()
        item_codes_metadata.append({
            "DocumentType": "IntermediateCodes",
            "Metadata": intermediate_codes
        })
        return item_codes_metadata

    def build_intermediate_details_static(self, intermediate_details: pd.DataFrame) -> list[dict]:
        json_string = str(intermediate_details.to_json(orient="records"))
        intermediate_details_list = json.loads(json_string)
        final_list = []
        for inter in intermediate_details_list:
            inter["ItemCode"] = inter["IntermediateCode"]
            inter["ItemName"] = inter["Intermediate"]
            inter["ItemType"] = "Intermediate"
            inter["DocumentType"] = "IntermediateDetail"
            final_list.append({
                "DocumentType": "IntermediateDetail",
                "Metadata": inter
            })
        return final_list

    def build_indicator_details_static(self, indicator_details: pd.DataFrame, intermediate_details: pd.DataFrame):
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
            indicator_detail["ItemCode"] = indicator_detail["IndicatorCode"]
            indicator_detail["ItemName"] = indicator_detail["Indicator"]
            indicator_detail["ItemType"] = "Indicator"
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
                    "ItemCode": indicator["CategoryCode"],
                    "ItemName": indicator["Category"],
                    "ItemType": "Category",
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

    def build_pillar_details_static(self, indicator_details: pd.DataFrame) -> list[dict]:
        json_string = str(indicator_details.to_json(orient="records"))
        indicator_details_list = json.loads(json_string)
        pillar_detail_map = {}
        for indicator in indicator_details_list:
            if indicator["PillarCode"] not in pillar_detail_map.keys():
                pillar_detail_map[indicator["PillarCode"]] = {
                    "ItemCode": indicator["PillarCode"],
                    "ItemName": indicator["Pillar"],
                    "ItemType": "Pillar",
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

    def build_sspi_detail_static(self, indicator_details: pd.DataFrame) -> list[dict]:
        json_string = str(indicator_details.to_json(orient="records"))
        indicator_details_list = json.loads(json_string)
        overall_detail = {
            "ItemCode": "SSPI",
            "ItemType": "SSPI",
            "ItemName": "Sustainable and Shared Prosperity Policy Index",
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
            {"DocumentType": "SSPIDetail", "Metadata": overall_detail}
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
            meta = detail["Metadata"]
            option_list.append({
                "Text": f"{meta['Indicator']} ({meta['IndicatorCode']})",
                "Value": "/data/indicator/" + meta["IndicatorCode"],
            })
        return option_list

    def category_options(self) -> list[str]:
        """
        Return a list of documents to build category options HTML for the dropdown
        """
        option_list = []
        for detail in self.find({"DocumentType": "CategoryDetail"}):
            meta = detail["Metadata"]
            option_list.append({
                "Text": f"{meta["Category"]} ({meta["CategoryCode"]})",
                "Value": "/data/category/" + meta["CategoryCode"],
            })
        return option_list

    def pillar_options(self) -> list[str]:
        """
        Return a list of documents to build pillar options HTML for the dropdown
        """
        option_list = []
        for detail in self.find({"DocumentType": "PillarDetail"}):
            meta = detail["Metadata"]
            option_list.append({
                "Text": f"{meta['Pillar']} ({meta['PillarCode']})",
                "Value": "/data/pillar/" + detail["Metadata"]["PillarCode"],
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

    def get_category_detail(self, CategoryCode: str) -> dict:
        """
        Return the detail for a particular category for CategoryCode
        """
        query = {
            "DocumentType": "CategoryDetail",
            "Metadata.CategoryCode": CategoryCode
        }
        return self.find_one(query)["Metadata"]

    def get_pillar_detail(self, PillarCode: str) -> dict:
        """
        Return the detail for a particular pillar for PillarCode
        """
        query = {
            "DocumentType": "PillarDetail",
            "Metadata.PillarCode": PillarCode
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
            "Metadata.ItemCode": ItemCode.upper(),
        })
        if not result:
            return {"Error": "ItemCode not found"}
        return result["Metadata"]
    

    def get_child_details(self, ItemCode: str) -> list[dict]:
        """
        Return a list of documents containing the details of the children of the given ItemCode

        :param ItemCode: The item code for which to get the children (SSPI, PillarCode, CategoryCode, IndicatorCode, IntermediateCode)
        """
        if ItemCode == "SSPI":
            return self.find({"DocumentType": "PillarDetail"})
        elif ItemCode in self.pillar_codes():
            return self.find({"DocumentType": "CategoryDetail", "Metadata.PillarCode": ItemCode})
        elif ItemCode in self.category_codes():
            return self.find({"DocumentType": "IndicatorDetail", "Metadata.CategoryCode": ItemCode})
        elif ItemCode in self.indicator_codes():
            return self.find({"DocumentType": "IntermediateDetail", "Metadata.IndicatorCode": ItemCode})
        elif ItemCode in self.intermediate_codes():
            return []
        else:
            return []


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

    def category_details(self, filter=[]) -> list[dict]:
        """
        Return a list of metadata dictionaries containing category details
        """
        flat_list = []
        for detail in self.find({"DocumentType": "CategoryDetail"}):
            if filter and detail["Metadata"]["CategoryCode"] not in filter:
                continue
            flat_list.append(detail["Metadata"])
        return flat_list

    def pillar_details(self, filter=[]) -> list[dict]:
        """
        Return a list of metadata dictionaries containing pillar details
        """
        flat_list = []
        for detail in self.find({"DocumentType": "PillarDetail"}):
            if filter and detail["Metadata"]["PillarCode"] not in filter:
                continue
            flat_list.append(detail["Metadata"])
        return flat_list

    def sspi_detail(self) -> dict:
        """
        Returns the metadata for the SSPI root item
        """
        return self.find_one({"DocumentType": "SSPIDetail"})["Metadata"]

    def pillar_category_summary_tree(self) -> list[dict]:
        """
        Returns a tree structure of pillars and categories
        """
        return self.find_one(
            {"DocumentType": "PillarCategorySummaryTree"}
        )["Metadata"] 

    def get_item_methodology_html(self, ItemCode: str) -> str:
        """
        Returns the HTML for the methodology of the given ItemCode
        """
        detail = self.get_item_detail(ItemCode)
        if "TreePath" not in detail.keys():
            return ""
        tree_path = detail["TreePath"].replace("sspi", "methodology")
        methodology_dirlst = ['..'] + tree_path.split('/') + ['methodology.md']
        methdology_fp = os.path.join(app.root_path, *methodology_dirlst)
        with open(methdology_fp, 'r', encoding='utf-8') as f:
            methodology = f.read()
        if not methodology:
            methodology_html = "<p>No methodology available for this item.</p>"
        try:
            post = frontmatter.loads(methodology)
            methodology_html = markdown(post.content, extensions=['fenced_code', 'tables'])
        except (ValueError, yaml.YAMLError) as e:
            raise MethodologyFileError(
                f"Error loading methodology file {methdology_fp}: {e};\n"
                "It is likely that there is an error in the YAML frontmatter format."
            )
        return methodology_html

    def item_details(self) -> list[dict]:
        sspi = self.sspi_detail()
        pillars = self.pillar_details()
        categories = self.category_details()
        indicators = self.indicator_details()
        return [ sspi ] + pillars + categories + indicators


