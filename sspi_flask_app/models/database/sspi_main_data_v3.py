from .mongo_wrapper import MongoWrapper
from flask import current_app as app
import pandas as pd
import os
import re
import json


class SSPIMainDataV3(MongoWrapper):

    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Raises an InvalidDocumentFormatError if the document is not 
        in the valid document format
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

