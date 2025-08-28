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
        Only includes items that have actual score data, not just metadata references
        """
        # Query for all items with actual scores (not null)
        country_data = self.find(
            {"CountryCode": sample_country, "Year": sample_year, "Score": {"$exists": True, "$ne": None}},
            {"_id": 0, "Children": 1, "ItemCode": 1, "ItemName": 1, "Score": 1}
        )
        if not country_data:
            raise ValueError(f"No data found for country {sample_country} in year {sample_year}.")
        
        # Build map of items that actually have score data
        item_map = {obs["ItemCode"]: obs for obs in country_data}
        items_with_data = set(item_map.keys())
        
        def build_tree(item_key):
            if not item_key:
                return None
            
            # Only process items that exist in our data
            if item_key not in item_map and item_key != "SSPI":
                return None
                
            node = item_map.get(item_key, {})
            children = []
            
            # Process children recursively
            for child_code in node.get("Children", []):
                child_node = build_tree(child_code)
                if child_node:
                    children.append(child_node)
            
            # Get the item name, using name_map as fallback
            item_name = node.get("ItemName")
            if not item_name or item_name == "":
                item_name = name_map.get(item_key, "")
            
            # For the root SSPI node, always include if it has children
            if item_key == "SSPI":
                if children:  # Only include SSPI if it has at least one child with data
                    return {
                        "ItemCode": item_key,
                        "ItemName": item_name,
                        "Children": children
                    }
                return None
            
            # For indicators (leaf nodes), include if they have a score
            if not node.get("Children", []):  # No children defined = likely an indicator
                if item_key in items_with_data:
                    return {
                        "ItemCode": item_key,
                        "ItemName": item_name,
                        "Children": []
                    }
                return None
            
            # For categories/pillars, only include if they have children with data
            if children:
                return {
                    "ItemCode": item_key,
                    "ItemName": item_name,
                    "Children": children
                }
            
            return None

        return build_tree("SSPI")

