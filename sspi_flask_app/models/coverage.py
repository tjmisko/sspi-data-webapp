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
        self.clean_data_coverage = self.get_clean_coverage()

    def get_clean_coverage(self):
        """
        Get the coverage of the clean data
        """
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "IndicatorCode": "$IndicatorCode",
                        "CountryCode": "$CountryCode"
                    },
                    "yearList": {
                        "$push": {
                            "$cond": [{"$gt": ["$Year", self.min_year]}, "$Year", "$$REMOVE"]
                        }
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "IndicatorCode": "$_id.IndicatorCode",
                    "CountryCode": "$_id.CountryCode",
                    "yearList": {
                        "$sortArray": {
                            "input": "$yearList",
                            "sortBy": 1
                        }
                    }
                }
            }
        ]
        return sspi_clean_api_data.aggregate(pipeline)
