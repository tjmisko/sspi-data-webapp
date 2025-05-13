from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_clean_api_data,
    sspi_imputed_data
)


class DataCoverage:
    def __init__(self, min_year: int, max_year: int, country_group: str, countries: list[str] = [], indicator_details: list[str] = []):
        self.min_year = min_year
        self.max_year = max_year
        self.country_group = country_group
        if not country_group and countries:
            self.countries = countries
        else:
            self.countries = sspi_metadata.country_group(country_group)
        if not indicator_details:
            self.indicator_details = sspi_metadata.indicator_details()
        else:
            self.indicator_details = indicator_details
        self.indicator_codes = [
            indicator["IndicatorCode"] for indicator in self.indicator_details
        ]
        self.clean_data_coverage = self.get_coverage(sspi_clean_api_data)
        self.imputed_data_coverage = self.get_coverage(sspi_imputed_data)

    def get_coverage(self, database):
        """
        Get the Year Coverage at the Indicator and Year Level
        :param database: The database to query
        """
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "IndicatorCode": "$IndicatorCode",
                        "CountryCode": "$CountryCode"
                    },
                    "yearList": {
                        "$addToSet": {
                            "$cond": [{"$gte": ["$Year", self.min_year]}, "$Year", "$$REMOVE"]
                        }
                    },
                }
            }
        ]
        result = database.aggregate(pipeline)
        nested_dict = {}
        for entry in result:
            ind = entry["_id"]["IndicatorCode"]
            ctry = entry["_id"]["CountryCode"]
            years = sorted(entry["yearList"])
            nested_dict.setdefault(ind, {})[ctry] = years
        return nested_dict
