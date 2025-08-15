from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
import frontmatter
from markdown import markdown
from sspi_flask_app.models.errors import InvalidDocumentFormatError, MethodologyFileError, DatasetFileError
from flask import current_app as app
import os
import json
import yaml
from bson import json_util
import pandas as pd
import logging

log = logging.getLogger(__name__)


class SSPIMetadata(MongoWrapper):

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
    
    def validate_item_detail_format(self, detail: dict):
        assert "ItemName" in detail.keys(), "ItemName is required in detail"
        assert "ItemCode" in detail.keys(), "ItemCode is required in detail"
        assert "ItemType" in detail.keys(), "ItemType is required in detail"
        if "LowerGoalpost" in detail.keys() and detail["LowerGoalpost"] is not None:
            assert type(detail["LowerGoalpost"]) in [int, float], "LowerGoalpost must be an int or float"
        if "UpperGoalpost" in detail.keys() and detail["UpperGoalpost"] is not None:
            assert type(detail["UpperGoalpost"]) in [int, float], "UpperGoalpost must be an int or float"
        if detail["ItemType"] not in ["SSPI", "Pillar", "Category", "Indicator", "Intermediate", "Dataset"]:
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
        elif detail["ItemType"] == "Indicator" and detail.get("DatasetCodes") is not None:
            assert type(detail["DatasetCodes"]) is list, "DatasetCodes must be a list"
            assert all(isinstance(code, str) for code in detail["DatasetCodes"]), "All DatasetCodes must be strings"

    def validate_dataset_detail_format(self, detail: dict):
        assert "DatasetName" in detail.keys(), "DatasetName is required in detail"
        assert "DatasetCode" in detail.keys(), "DatasetCode is required in detail"
        assert "DatasetType" in detail.keys(), "DatasetType is required in detail"

    def load(self) -> int:
        local_path = os.path.join(os.path.dirname(app.instance_path), "local")
        with open(os.path.join(local_path, "country-groups.json")) as file:
            country_groups = json.load(file)
        with open(os.path.join(local_path, "country-flag-colors.json")) as file:
            country_colors = json.load(file)
        with open(os.path.join(local_path, "sspi-colors.json")) as file:
            sspi_custom_colors = json.load(file)
        count = self.load_dynamic(
            country_groups,
            country_colors,
            sspi_custom_colors
        )
        return count

    def load_dynamic(self, country_groups, country_colors, sspi_custom_colors) -> int:
        """
        Load metadata specified in methodology files into the database

        Canonical order of indicators is specified by the order given in the
        parent list.
        """
        dataset_details = self.load_dataset_files()
        dataset_details.sort(key=lambda x: x["DatasetCode"])
        source_details = self.generate_source_details(dataset_details)
        source_details.sort(key=lambda x: x["Metadata"]["DatasetCodes"][0])
        item_details = self.load_methodology_files()
        for detail in item_details:
            detail["DocumentType"] = detail["ItemType"] + "Detail"
        item_codes = {
            "SSPI": [],
            "Pillar": [],
            "Category": [],
            "Indicator": []
        }
        sorted_item_details = self.sort_item_details(item_details)
        pc_sum_tree = self.build_pillar_category_summary_tree(sorted_item_details)
        for detail in sorted_item_details:
            item_codes[detail["Metadata"]["ItemType"]].append(detail["Metadata"]["ItemCode"])
        metadata = []
        metadata.extend([
            {"DocumentType": "PillarCodes", "Metadata": item_codes["Pillar"]},
            {"DocumentType": "CategoryCodes", "Metadata": item_codes["Category"]},
            {"DocumentType": "IndicatorCodes", "Metadata": item_codes["Indicator"]},
            {"DocumentType": "DatasetCodes", "Metadata": [d["DatasetCode"] for d in dataset_details]},
        ])
        metadata.extend(self.build_country_groups(country_groups))
        metadata.extend(self.build_country_details(country_groups, country_colors, sspi_custom_colors))
        metadata.extend(sorted_item_details)
        metadata.extend(source_details)
        metadata.extend([{
            "DocumentType": "DatasetDetail",
            "Metadata": d
        } for d in dataset_details])
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
        indicators = []
        categories = []
        pillars_sorted = []
        for detail in details:
            if detail["ItemType"] == "SSPI":
                pillars_sorted = detail["PillarCodes"]
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
        categories.sort(key=lambda x: pillars_sorted.index(x["PillarCode"]))
        categories_sorted = [cat for p_list in categories for cat in p_list["List"]]
        indicators.sort(key=lambda x: categories_sorted.index(x["CategoryCode"]))
        indicators_sorted = [ind for c_list in indicators for ind in c_list["List"]]
        n_details = 1 + len(pillars_sorted) + len(categories_sorted) + \
            len(indicators_sorted)
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
            else:
                raise MethodologyFileError(
                    f"Invalid ItemType {detail['ItemType']} in detail {detail}"
                )
            sorted_details[insert_index] = detail
        assert all([isinstance(d, dict) for d in sorted_details]), "All details must be dictionaries"
        expected_details = ["SSPI"] + pillars_sorted + categories_sorted + indicators_sorted
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
        print("Methodology Directory: ", method_dir)
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
                    continue
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
                self.validate_item_detail_format(detail)
                details.append(detail)
        return details

    def load_dataset_files(self) -> list:
        """
        Walks through the dataset directory and loads the frontmatter
        of all dataset files
        :return: A list of dictionaries containing the metadata from the dataset files
        """
        dataset_dir = os.path.join(os.path.dirname(app.instance_path), "datasets")
        print("Dataset Directory: ", dataset_dir)
        details = []
        for dirpath, dirnames, filenames in os.walk(dataset_dir):
            for dataset_file in filenames:
                if dataset_file and not dataset_file == "documentation.md":
                    continue
                full_dataset_path = os.path.join(dirpath, dataset_file)
                try:
                    detail = frontmatter.load(full_dataset_path)
                except (ValueError, yaml.YAMLError) as e:
                    raise DatasetFileError(
                        f"Error loading dataset file {full_dataset_path}: {e};\n"
                        "It is likely that there is an error in the YAML frontmatter format."
                    )
                detail = detail.metadata
                self.validate_dataset_detail_format(detail)
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

    def generate_source_details(self, dataset_details: list[dict]) -> list[dict]:
        """
        Generates source details from dataset details. Used to lookup 
        the list of datasets that depend on a given source name.
        """
        source_to_ds_map = {}
        for detail in dataset_details:
            if "Source" not in detail.keys():
                raise DatasetFileError(
                    f"Dataset {detail['DatasetCode']} does not have a 'Source' field. "
                    "Please ensure that all dataset files have a 'Source' field in the YAML frontmatter."
                )
            if not isinstance(detail["Source"], dict):
                raise DatasetFileError(
                    f"Dataset {detail['DatasetCode']} has an invalid 'Source' field. "
                    "The 'Source' field YAML must evaluate to a 'dict' in python."
                )
            hashable_source = tuple(sorted(detail["Source"].items()))
            if hashable_source not in source_to_ds_map:
                source_to_ds_map[hashable_source] = []
            source_to_ds_map[hashable_source].append(detail["DatasetCode"])
        return [
            {
                "DocumentType": "SourceDetail",
                "Metadata": {
                    "Source": dict(source),
                    "DatasetCodes": dataset_codes
                }
            } for source, dataset_codes in source_to_ds_map.items()
        ]

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

    def item_codes(self) -> list[str]:
        item_code_list = ["SSPI"]
        item_code_list.extend(self.indicator_codes())
        item_code_list.extend(self.category_codes())
        item_code_list.extend(self.pillar_codes())
        return item_code_list

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

    def dataset_details(self) -> list[dict]:
        """
        Return a list of documents containg dataset details
        """
        flat_list = []
        for detail in self.find({"DocumentType": "DatasetDetail"}):
            flat_list.append(detail["Metadata"])
        return flat_list

    def dataset_codes(self) -> list[str]:
        """
        Return a list of documents containg dataset details
        """
        result = self.find_one({"DocumentType": "DatasetCodes"})
        if not result:
            return []
        return result.get("Metadata", [])

    def get_dataset_detail(self, DatasetCode: str) -> dict:
        """
        Return a document containing indicator details for a specific IndicatorCode
        """
        query = {
            "DocumentType": "DatasetDetail",
            "Metadata.DatasetCode": DatasetCode
        }
        return self.find_one(query)["Metadata"]

    def get_series_type(self, series_code: str) -> str|None:
        """
        """
        if series_code in self.dataset_codes():
            return "Dataset"
        elif series_code in self.item_codes():
            return "Item"
        else:
            return None

    def get_item_detail(self, ItemCode: str) -> dict:
        """
        Return a document containing the item details for a specific ItemCode

        :param ItemCode: The item code for which to get the details (SSPI, PillarCode, CategoryCode, IndicatorCode, DatasetCode)
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

        :param ItemCode: The item code for which to get the children (SSPI, PillarCode, CategoryCode, IndicatorCode, DatasetCode)
        """
        if ItemCode == "SSPI":
            return self.find({"DocumentType": "PillarDetail"})
        elif ItemCode in self.pillar_codes():
            category_codes = self.get_pillar_detail(ItemCode)["Children"]
            return self.find({"DocumentType": "CategoryDetail", "Metadata.ItemCode": {"$in": category_codes}})
        elif ItemCode in self.category_codes():
            indicator_codes = self.get_category_detail(ItemCode)["Children"]
            return self.find({"DocumentType": "IndicatorDetail", "Metadata.ItemCode": {"$in": indicator_codes}})
        elif ItemCode in self.indicator_codes():
            detail = self.get_indicator_detail(ItemCode)  # Ensure the indicator exists
            child_codes = detail.get("DatasetCodes", [])
            return self.find({"DocumentType": "DatasetDetail", "Metadata.DatasetCode": {"$in": child_codes}})
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

    def get_dataset_dependencies(self, series_code: str) -> list:
        """
        Returns the list of datasets on which the provided series_code depends
        """
        series_type = self.get_series_type(series_code)
        if series_type == "Dataset":
            return [ series_code ]
        elif series_type == "Item":
            children = self.get_item_detail(series_code).get("Children", [])
            if not children and series_code in self.indicator_codes():
                children = self.get_indicator_detail(series_code).get("DatasetCodes", [])
            assert not any([c is None for c in children])
            dataset_dependencies = []
            for c in children:
                dataset_dependencies = dataset_dependencies + self.get_dataset_dependencies(c)
            return dataset_dependencies   
        else:
            return []

    def get_source_info(self, dataset_code: str) -> dict:
        """
        Returns the source information for the given dataset code
        """
        detail = self.get_dataset_detail(dataset_code)
        if not detail:
            raise ValueError(f"Dataset code {dataset_code} not found in metadata.")
        return detail["Source"]

    def get_downstream_datasets(self, source_info: dict) -> list[str]:
        """
        Returns a list of dataset codes that depend on the given source information
        """
        source_query = {}
        for k,v in source_info.items():
            source_query["Metadata.Source." + k] = v
        source_query["DocumentType"] = "SourceDetail"
        source_detail = self.find_one(source_query)
        if not source_detail:
            return []
        return source_detail["Metadata"]["DatasetCodes"]

    def sspi_detail(self) -> dict:
        """
        Returns the detail for the SSPI item
        """
        sspi_detail = self.find_one({"DocumentType": "SSPIDetail"})
        if not sspi_detail:
            raise ValueError("SSPI detail not found in metadata.")
        return sspi_detail["Metadata"]

    def item_details(self, indicator_filter: list[str]=[]) -> list[dict]:
        """
        Returns a list of all item details, including SSPI, Pillars, Categories, and Indicators.
        If a filter is provided, only items with codes in the filter will be returned.
        
        :param filter: A list of item codes to filter the results. If empty, all item details will be returned.
        """
        sspi = self.sspi_detail()
        pillars = self.pillar_details()
        categories = self.category_details()
        indicators = self.indicator_details()
        if indicator_filter:
            indicators_filtered = [i for i in indicators if i["IndicatorCode"] in indicator_filter]
            categories_filtered = []
            for c in categories:
                contained_indicators = [i for i in c["IndicatorCodes"] if i in indicator_filter]
                if len(contained_indicators) > 0:
                    c["IndicatorCodes"] = contained_indicators
                    categories_filtered.append(c)
            pillars_filtered = []
            for p in pillars:
                implied_category_filter = [c["CategoryCode"] for c in categories_filtered]
                contained_categories = [c for c in p["CategoryCodes"] if c in implied_category_filter]
                if len(contained_categories) > 0:
                    p["CategoryCodes"] = contained_categories
                    pillars_filtered.append(p)
            implied_pillar_filter = [p["PillarCode"] for p in pillars_filtered]
            sspi["PillarCodes"] = implied_pillar_filter
            return [ sspi ] + pillars_filtered + categories_filtered + indicators_filtered
        return [ sspi ] + pillars + categories + indicators

    def record_dataset_range(self, clean_dataset: list[dict], dataset_code: str):
        """
        Records the range of values for a dataset in the metadata collection.
        This is used to track the temporal coverage of datasets.

        :param clean_dataset: The cleaned dataset to record the range for.
        :param dataset_code: The code of the dataset to record the range for.
        """
        min_val, max_val = 0, 0
        for d in clean_dataset:
            new_val = d.get("Value")
            assert isinstance(new_val, (int, float)), (
                f"Value for dataset {dataset_code} must be an int or float, "
                f"but found {type(new_val)}: {new_val}"
            )
            if new_val > max_val:
                max_val = new_val
            elif new_val < min_val:
                min_val = new_val
        query = {
            "DocumentType": "DatasetDetail",
            "Metadata.DatasetCode": dataset_code
        }
        self._mongo_database.update_one(
            query,
            {"$set": {
                "Metadata.Range.yMin": min_val,
                "Metadata.Range.yMax": max_val
            }}
        )

