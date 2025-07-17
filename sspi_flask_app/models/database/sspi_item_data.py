from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper


class SSPIItemData(MongoWrapper):

    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        """
        self.validate_country_code(document, document_number)
        self.validate_item_code(document, document_number)
        self.validate_year(document, document_number)
        self.validate_score(document, document_number)

    def active_schema(self, sample_country="USA", sample_year=2018, name_map: dict={}) -> dict:
        """
        Return the SSPI Schema used to score the documents
        """
        country_data = self.find(
            {"CountryCode": sample_country, "Year": sample_year},
            {"_id": 0, "Children": 1, "ItemCode": 1, "ItemName": 1}
        )
        if not country_data:
            raise ValueError(f"No data found for country {sample_country} in year {sample_year}.")
        item_map = {obs["ItemCode"]: obs for obs in country_data}
        def build_tree(item_key):
            node = item_map.get(item_key, {})
            return [{
                "ItemCode": item_key,
                "ItemName": node.get("ItemName", name_map.get(item_key, "")),
                "Children": [build_tree(child) for child in node.get("Children", [])]
            }] if item_key else []
        return build_tree("SSPI")[0]
