from abc import abstractmethod
from sspi_flask_app.api.resources.utilities import detect_repeated_item
from sspi_flask_app.models.errors import (
    InvalidDocumentFormatError,
    DataMetadataMismatchError
)
import logging
log = logging.getLogger(__name__)

class SSPI:
    def __init__(self, item_details: list[dict], indicator_scores: list[dict], strict_year: bool = True):
        """
        Generate SSPI scores for a country and year

        :param item_details: Expects a list of dictionaries in Metadata format (see sspi_metadata)
        :param indicator_scores: Expects a list of dictionaries of scores for a given country
        """
        self.item_details = item_details
        self.indicator_scores = indicator_scores
        self.strict_year = strict_year
        self.load_structure()
        self.validate_input_assumptions()
        self.score()

    def load_structure(self):
        self.pillars = []
        self.categories = []
        self.indicators = []
        self._item_detail_table = {}
        self.root = None
        for item in self.item_details:
            item_type = item.get('ItemType', None)
            item_code = item.get('ItemCode', None)
            if not item_type or not item_code:
                msg = f"Missing ItemType and/or ItemCode in item details: {item}"
                raise InvalidDocumentFormatError(msg)
            if item_type == 'SSPI':
                item_obj = Root(item)
                self.root = item_obj
            elif item_type == 'Pillar':
                item_obj = Pillar(item)
                self.pillars.append(item_obj)
            elif item_type == 'Category':
                item_obj = Category(item)
                self.categories.append(item_obj)
            elif item_type == 'Indicator':
                item_obj = Indicator(item)
                self.indicators.append(item_obj)
            else:
                msg = f"Unknown ItemType {item_type} in item details."
                raise InvalidDocumentFormatError(msg)
            self._item_detail_table[item_code] = item_obj 
        self.items = [self.root] + self.pillars + self.categories + self.indicators

    def validate_input_assumptions(self):
        if self.strict_year:
            assert [s['Year'] for s in self.indicator_scores], \
            "Year must be specified in indicator_scores"
        if not self.root: # SSPI root item not found in item details (for Static Back-Compatibility)
            self.root = Root({
                "Description": "The Sustainable and Shared Proseperity Index scores national policies across three pillars: Sustainability, Market Structure, and Public Goods\n",
                "DocumentType": "SSPIDetail",
                "ItemCode": "SSPI",
                "ItemName": "Sustainable and Shared Prosperity Policy Index",
                "ItemOrder": 0,
                "ItemType": "SSPI",
                "PillarCodes": [
                    "SUS",
                    "MS",
                    "PG"
                ],
                "ShortDescription": "The Sustainable and Shared Proseperity Index scores national policies across three pillars: Sustainability, Market Structure, and Public Goods\n",
                "TreePath": "sspi"
            })
        if self.strict_year:
            # Fragile design: enforce year consistency when strict_year=True
            years = [ind.get('Year') for ind in self.indicator_scores]
            assert all(y is not None for y in years), "All indicator scores must have Year specified"
            unique_years = set(years)
            assert len(unique_years) == 1, f"All indicators must have same year, got: {unique_years}"
            self.year = years[0]
        else:
            # For non-strict mode (e.g., static rank data), handle mixed years gracefully
            years = [ind.get('Year') for ind in self.indicator_scores if ind.get('Year') is not None]
            self.year = years[0] if years else 2018  # Fallback for non-strict mode only
        
        for ind in self.indicator_scores:
            ind_item = self._item_detail_table.get(ind['IndicatorCode'], None)
            if not ind_item:
                raise DataMetadataMismatchError(
                    f"IndicatorCode {ind['IndicatorCode']} not found in item details."
                )
            ind_item.score = ind.get('Score', None)
            ind_item.year = ind.get('Year', None)
            if self.strict_year:
                assert ind_item.year is not None, \
                    f"Year for indicator {ind['IndicatorCode']} is missing in indicator_scores."
            else:
                # For non-strict mode, set default year if missing
                if ind_item.year is None:
                    ind_item.year = self.year
            assert ind_item.score is not None, \
                f"Score for indicator {ind['IndicatorCode']} is missing in indicator_scores."
        
        # Set year on ALL items (categories, pillars, root) - fragile design requires consistency
        for item in self._item_detail_table.values():
            if not hasattr(item, 'year') or item.year is None:
                item.year = self.year
        
        if len(self.indicators) != len(self.indicator_scores):
            indicator_codes_metadata = [i.code for i in self.indicators]
            indicator_codes_data = [str(d.get("IndicatorCode")) for d in self.indicator_scores]
            symmetric_diff = set(indicator_codes_metadata) ^ set(indicator_codes_data)
            country_code = self.indicator_scores[0].get("CountryCode", None)
            year = self.year or "Missing"
            raise DataMetadataMismatchError(
                "Number of indicator codes does not match number of indicator scores:"
                f" {len(self.indicators)} vs {len(self.indicator_scores)}\n"
                f"CountryCode: {country_code}\n"
                f"Year: {year}\n"
                f"Symmetric difference: {symmetric_diff}\n"
                f"Repeats in Metadata Codes: {detect_repeated_item(indicator_codes_metadata)}\n"
                f"Repeats in Data Codes: {detect_repeated_item(indicator_codes_data)}\n"
                f"Metadata codes: {sorted(indicator_codes_metadata)}\n"
                f"Data codes: {sorted(indicator_codes_data)}"
                f"CountryCode: {self.indicator_scores[0].get('CountryCode', '')}"
            )

    def score(self):
        for cat in self.categories:
            if not cat.indicator_codes:
                raise InvalidDocumentFormatError(
                    f"Category {cat} has no indicators defined."
                )
            catsum = sum([self._item_detail_table[ic].score for ic in cat.indicator_codes])
            catlen = len(cat.indicator_codes)
            cat.score = catsum / catlen
        for pil in self.pillars:
            if not pil.category_codes:
                raise InvalidDocumentFormatError(
                    f"Pillar {pil} has no categories defined."
                )
            pilsum = sum([self._item_detail_table[cc].score for cc in pil.category_codes])
            pillen = len(pil.category_codes)
            pil.score = pilsum / pillen
        self.root.score = sum([self._item_detail_table[p.code].score for p in self.pillars]) / len(self.pillars)
        assert all([it.score is not None for it in self._item_detail_table.values()]), \
            "Not all items have a score calculated."

    def get_item(self, item_code: str) -> dict:
        """
        Get item by item code.

        :param item_code: The code of the item to retrieve.
        :return: The item details and score as a dictionary.
        """
        item = self._item_detail_table.get(item_code, None)
        if not item:
            raise KeyError(f"ItemCode {item_code} not found in item details.")
        return item

    def to_rank_dict(self, country_code: str, year: int) -> dict:
        """Export all items as dictionaries suitable for ranking"""
        rank_dict = {}
        for item in self.items:
            rank_dict[item.code] = {
                "ICode": item.code,
                "IName": item.name,
                "CCode": country_code,
                "Year": year,
                "Score": item.score,
            }
        return rank_dict

    def get_all_items(self) -> list:
        """Get all items (pillars, categories, indicators) as a flat list"""
        return list(self._item_detail_table.values())

    def to_score_documents(self, country_code: str) -> list[dict]:
        """Generate score documents for database insertion"""
        docs = []
        for item in self._item_detail_table.values():
            if item.score is not None:
                # Fragile design: crash if any item lacks year instead of defaulting
                assert hasattr(item, 'year') and item.year is not None, \
                    f"Item {item.code} missing year - invalid state"
                docs.append({
                    "CountryCode": country_code,
                    "ItemCode": item.code,
                    "ItemType": item.type,
                    "Score": item.score,
                    "Year": item.year
                })
        return docs

class Item:
    def __init__(self, item_detail: dict):
        self.code = item_detail.get('ItemCode')
        self.name = item_detail.get('ItemName', self.code)
        self.type = item_detail.get('ItemType')
        self.score = item_detail.get('Score', None)


class Root(Item):
    def __init__(self, item_detail: dict):
        super().__init__(item_detail)
        self.pillar_codes = item_detail.get('PillarCodes', [])

class Pillar(Item):
    def __init__(self, item_detail: dict):
        super().__init__(item_detail)
        self.category_codes = item_detail.get('CategoryCodes', [])

class Category(Item):
    def __init__(self, item_detail: dict):
        super().__init__(item_detail)
        self.indicator_codes = item_detail.get('IndicatorCodes', [])

class Indicator(Item):
    def __init__(self, item_detail: dict):
        super().__init__(item_detail)
