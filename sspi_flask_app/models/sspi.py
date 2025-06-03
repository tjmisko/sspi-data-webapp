from sspi_flask_app.models.errors import (
    InvalidDocumentFormatError,
    DataOrderError
)


class SSPI:
    def __init__(self, indicator_details: list[dict], indicator_scores: list[dict], strict_year: bool = True):
        """
        Generate SSPI scores for a country and year

        :param indicator_details: Expects a list of dictionaries in Metadata format (see sspi_metadata)
        :param indicator_scores: Expects a list of dictionaries of scores for a given country
        """
        self._indicator_details = indicator_details
        self._indicator_scores = indicator_scores
        mismatch = "{} mismatch detected in indicator_scores"
        assert all([indicator_scores[i]["CountryCode"] == indicator_scores[0]["CountryCode"]
                    for i in range(len(indicator_scores))]), mismatch.format("CountryCode")
        if strict_year:
            assert all([indicator_scores[i]["Year"] == indicator_scores[0]["Year"]
                        for i in range(len(indicator_scores))]), mismatch.format("Year")
        self.country_code = indicator_scores[0]["CountryCode"]
        self.year = indicator_scores[0]["Year"]
        self.pillars = []
        self.load(indicator_details, indicator_scores)
        self.categories = []
        for p in self.pillars:
            self.categories += p.categories
        self.indicators = []
        for c in self.categories:
            self.indicators += c.indicators

    def score(self) -> float:
        return sum([pillar.score() for pillar in self.pillars]) / len(self.pillars)

    def score_tree(self):
        tree = {"SSPI": {"Score": self.score(), "Pillars": []}}
        for i, pillar in enumerate(self.pillars):
            tree["SSPI"]["Pillars"].append({
                "Pillar": pillar.name,
                "PillarCode": pillar.code,
                "Score": pillar.score(),
                "Categories": []
            })
            for j, category in enumerate(pillar.categories):
                tree["SSPI"]["Pillars"][i]["Categories"].append({
                    "Category": category.name,
                    "CategoryCode": category.code,
                    "Score": category.score(),
                    "Indicators": []
                })
                for indicator in category.indicators:
                    tree["SSPI"]["Pillars"][i]["Categories"][j]["Indicators"].append({
                        "Indicator": indicator.name,
                        "IndicatorCode": indicator.code,
                        "Score": indicator.score,
                        "Year": indicator.year
                    })
        return tree

    def score_documents(self) -> list[dict]:
        """
        Returns a list of documents with the scores for at each level.

        Document Structure:
        {
            CountryCode: CountryCode
            ItemCode: SSPI | PillarCode | CategoryCode | IndicatorCode
            ItemType: SSPI | Pillar | Category | Indicator
            ItemName: Name of the item
            Score: Score of the item
            Year: Year of the score
            CumulativeImputationDistance: pass
            AverageImputationDistance: pass
            EstimatedImputationError: pass
        }
        """
        documents = []
        identifiers = {
            "CountryCode": self.country_code,
            "Year": self.year,
        }
        overall = {
            "ItemCode": "SSPI",
            "ItemType": "SSPI",
            "ItemName": "Sustainable and Shared-Prosperity Policy Index",
            "Score": self.score(),
            "Children": [p.code for p in self.pillars]
        }
        overall.update(identifiers)
        documents.append(overall)
        for pillar in self.pillars:
            pillar_doc = {
                "ItemCode": pillar.code,
                "ItemType": "Pillar",
                "ItemName": pillar.name,
                "Score": pillar.score(),
                "Children": [c.code for c in pillar.categories]
            }
            pillar_doc.update(identifiers)
            documents.append(pillar_doc)
            for category in pillar.categories:
                category_doc = {
                    "ItemCode": category.code,
                    "ItemType": "Category",
                    "ItemName": category.name,
                    "Score": category.score(),
                    "Children": [i.code for i in category.indicators]
                }
                category_doc.update(identifiers)
                documents.append(category_doc)
        return documents

    def pillar_scores(self):
        return {pillar.code: pillar.score() for pillar in self.pillars}

    def category_scores(self):
        return {category.code: category.score() for category in self.categories}

    def indicator_scores(self):
        return {indicator.code: indicator.score for indicator in self.indicators}

    def extract_score(self, IndicatorCode: str, indicator_scores: list):
        for indicator in indicator_scores:
            if indicator["IndicatorCode"] == IndicatorCode:
                return indicator["Score"]
        return None

    def load(self, indicator_details, indicator_scores):
        if len(indicator_details) != len(indicator_scores):
            details = sorted([d["IndicatorCode"]
                           for d in indicator_details])
            scores = sorted([s["IndicatorCode"] for s in indicator_scores])
            error_msg = (
                f"Length of indicator_details {len(indicator_details)} and "
                f"indicator_scores {len(indicator_scores)} must match!"
                f"\nDetail Codes: {details}\nScore Codes: {scores}\n\n"
                f"Score Data: {indicator_scores}"
            )
            raise DataOrderError(error_msg)

        indicator_score_lookup = {}
        for i in indicator_scores:
            indicator_score_lookup[i["IndicatorCode"]] = i
        for detail in indicator_details:
            try:
                indicator_code = detail["IndicatorCode"]
                indicator_score = indicator_score_lookup[indicator_code]
            except KeyError:
                error_msg = f"No data for indicator {indicator_code} found!"
                raise DataOrderError(error_msg)
            matched_pillar = self.get_pillar(detail["PillarCode"])
            if not matched_pillar:
                matched_pillar = Pillar(detail, indicator_score)
                self.pillars.append(matched_pillar)
            matched_pillar.load(detail, indicator_score)

    def get_pillar(self, pillar_code):
        """
        Takes in a PillarCode and returns the matching pillar object.
        Returns None if no match exists
        """
        for pillar in self.pillars:
            if pillar_code == pillar.code:
                return pillar
        return None

    def get_category(self, CategoryCode):
        pass

    def get_indicator(self, IndicatorCode):
        """
        Better to tree search, or to build a lookup table first?
        - This is going to be run a bunch of times when we add scores.
        - Potentially going to be run on request or for AJAX, so needs
        to be pretty fast.
        - Tree search once to build index, then use it a 57 times per country per year...
        """
        pass


class Pillar:
    def __init__(self, detail: dict, indicator_score: dict):
        self.name = detail["Pillar"]
        self.code = detail["PillarCode"]
        self.categories = []
        self.load(detail, indicator_score)

    def __repr__(self):
        return f"Pillar<{self.code}: {self.score()}; {self.categories}"

    def __str__(self):
        return f"Pillar<{self.code}: {self.score()}; {self.categories}"

    def score(self):
        return sum([category.score() for category in self.categories])/len(self.categories)

    def load(self, detail, indicator_score):
        """
        When called the first time (from the constructor) it loads the first category from the detail.
        Successive calls load additional categories or revise existing categories with new data
        """
        matched_category = self.get_category(
            detail["CategoryCode"])
        if matched_category:
            matched_category.load(detail, indicator_score)
        else:
            matched_category = Category(detail, indicator_score)
            self.categories.append(matched_category)

    def get_category(self, category_code):
        for category in self.categories:
            if category_code == category.code:
                return category
        return None


class Category:
    def __init__(self, detail: dict, indicator_score_data: dict):
        self.name = detail["Category"]
        self.code = detail["CategoryCode"]
        self.indicators = []
        self.load(detail, indicator_score_data)

    def __repr__(self):
        return f"Category<{self.code}: {self.score()}; {self.indicators}"

    def __str__(self):
        return f"Category<{self.code}: {self.score()}; {self.indicators}"

    def score(self):
        return sum([indicator.score for indicator in self.indicators])/len(self.indicators)

    def load(self, detail: dict, indicator_score_data: dict):
        """
        When called the first time (from the constructor) it loads the first indicator from the detail.
        Successive calls load additional indicator
        """
        matched_indicator = self.get_indicator(
            detail["IndicatorCode"])
        if matched_indicator:
            matched_indicator.load(detail, indicator_score_data)
        else:
            new_indicator = Indicator(detail, indicator_score_data)
            self.indicators.append(new_indicator)

    def get_indicator(self, indicator_code):
        for indicator in self.indicators:
            if indicator.code == indicator_code:
                return indicator
        return None


class Indicator:
    def __init__(self, detail, indicator_score_data):
        self.load(detail, indicator_score_data)

    def __repr__(self):
        return f"Indicator<{self.code}: {self.score}>"

    def __str__(self):
        return f"Indicator<{self.code}: {self.score}>"

    def load(self, detail, indicator_score_data):
        try:
            self.name = detail["Indicator"]
            self.code = detail["IndicatorCode"]
            self.lower_goalpost = detail["LowerGoalpost"]
            self.upper_goalpost = detail["UpperGoalpost"]
        except KeyError as ke:
            msg = (
                f"Indicator Detail Missing Name or Indicator "
                f"Code {detail} ({ke})"
            )
            raise InvalidDocumentFormatError(msg)
        try:
            self.score = indicator_score_data["Score"]
            self.value = indicator_score_data["Value"]
            self.year = indicator_score_data["Year"]
        except KeyError as ke:
            msg = (
                f"Indicator Data Missing 'Score', 'Value', or 'Year'"
                f"({indicator_score_data}) ({ke})"
            )
            raise InvalidDocumentFormatError(msg)
        if self.code != indicator_score_data["IndicatorCode"]:
            msg = (
                f"Mismatched Data and Indicator Detail {detail}; "
                f"{indicator_score_data}"
            )
            raise DataOrderError(msg)
        if type(self.score) is float:
            if self.score < 0 or self.score > 1:
                raise InvalidDocumentFormatError(
                    f"Score is not between 0 and 1! ({self})")
