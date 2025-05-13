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
        self.combined_coverage = self.union(
            self.clean_data_coverage, self.imputed_data_coverage
        )

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

    def union(self, cov_dict1: dict, cov_dict2: dict):
        """
        Compute the union of two coverage dictionaries to find their combined
        coverage
        :param cov_dict1: The first coverage dictionary (output format of get_coverage)
        :param cov_dict2: The second coverage dictionary (output format of get_coverage)
        """
        merged = {}
        for ind_code in set(cov_dict1.keys()).union(cov_dict2.keys()):
            merged.setdefault(ind_code, {})
            countries1 = cov_dict1.get(ind_code, {})
            countries2 = cov_dict2.get(ind_code, {})
            for ctry_code in set(countries1.keys()).union(countries2.keys()):
                years1 = set(countries1.get(ctry_code, []))
                years2 = set(countries2.get(ctry_code, []))
                merged[ind_code][ctry_code] = sorted(years1.union(years2))
        return merged

    def check_complete_country(self, year_list):
        """
        Check whether the coverage is complete for a given country
        :param year_list: The list of years for a given country, given as the
        value of the CountryCode key in the coverage dictionary
        """
        return all([
            year in range(self.min_year, self.max_year + 1)
            for year in year_list
        ])

    def check_complete_indicator(self, country_year_dict):
        """
        Check whether the coverage is complete for a given indicator
        :param country_year_dict: The dictionary of countries and years for a
        given indicator, given as the value of the IndicatorCode key in the
        coverage dictionary
        """
        return all([
            self.check_complete_country(year_list)
            for year_list in country_year_dict.values()
        ])

    def complete(self):
        complete_list = []
        for indicator in self.indicator_codes:
            if indicator not in self.combined_coverage.keys():
                continue
            country_year_dict = self.combined_coverage[indicator]
            if self.check_complete_indicator(country_year_dict):
                complete_list.append(indicator)
        return complete_list

    def incomplete(self):
        incomplete_list = []
        for indicator in self.indicator_codes:
            if indicator not in self.combined_coverage.keys():
                continue
            country_year_dict = self.combined_coverage[indicator]
            if not self.check_complete_indicator(country_year_dict):
                incomplete_list.append(indicator)
        return incomplete_list
