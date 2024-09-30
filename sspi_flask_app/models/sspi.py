from .errors import InvalidDocumentFormatError, DataOrderError

class SSPI:
    def __init__(self, indicator_details:list[dict], indicator_scores:list[dict]):
        """
        indicator_details - Expects a list of dictionaries in Metadata format (see sspi_metadata)
        country_scores - Expects a list of dictionaries of scores for a given country
        - [ ] To-do @tjmisko: set up to handle years, maybe with an SSPIDynamic Object with SSPI objects
        - [ ] How might it make sense to do this? Keep one object in memory and run different lists of data through it to put in new data based on that instead of building a new object fresh every time
        """
        self._indicator_details = indicator_details
        self._indicator_scores = indicator_scores
        self.pillars = []
        self.load(indicator_details, indicator_scores)
        self.categories = []
        for p in self.pillars:
            self.categories += p.categories
        self.indicators = []
        for c in self.categories:
            self.indicators += c.indicators

    def score(self) -> float:
        return sum([pillar.score() for pillar in self.pillars])/len(self.pillars)
    
    def score_tree(self):
        tree = {"SSPI": {"Score": self.score(), "Pillars": []}}
        for i, pillar in enumerate(self.pillars):
            tree["SSPI"]["Pillars"].append({"Pillar": pillar.name, "PillarCode": pillar.code, "Score": pillar.score(), "Categories": []})
            for j, category in enumerate(pillar.categories):
                tree["SSPI"]["Pillars"][i]["Categories"].append({"Category": category.name, "CategoryCode": category.code, "Score": category.score(), "Indicators": []})
                for indicator in category.indicators:
                    tree["SSPI"]["Pillars"][i]["Categories"][j]["Indicators"].append({"Indicator": indicator.name, "IndicatorCode": indicator.code, "Score": indicator.score})
        return tree

    def pillar_scores(self):
        return {pillar.code: pillar.score() for pillar in self.pillars}

    def category_scores(self):
        return {category.code: category.score() for category in self.categories}

    def indicator_scores(self):
        return {indicator.code: indicator.score for indicator in self.indicators}

    def extract_score(self, IndicatorCode:str, indicator_scores:list):
        for indicator in indicator_scores:
            if indicator["IndicatorCode"] == IndicatorCode:
                return indicator["Score"]
        return None

    def load(self, indicator_details, indicator_scores):
        if len(indicator_details) != len(indicator_scores):
            raise DataOrderError(f"Length of indicator_details {len(indicator_details)} and indicator_scores {len(indicator_scores)} must match!")
        indicator_score_lookup = {}
        for i in indicator_scores:
            indicator_score_lookup[i["IndicatorCode"]] = i
        for detail in indicator_details:
            try:
                indicator_score = indicator_score_lookup[detail["Metadata"]["IndicatorCode"]]
            except KeyError:
                indicator = detail["Metadata"]["IndicatorCode"]
                raise DataOrderError(f"No data for indicator {indicator} found!")
            matched_pillar = self.get_pillar(detail["Metadata"]["PillarCode"])
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
    def __init__(self, detail:dict, indicator_score:dict):
        self.name = detail["Metadata"]["Pillar"]
        self.code = detail["Metadata"]["PillarCode"]
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
        matched_category = self.get_category(detail["Metadata"]["CategoryCode"])
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
    def __init__(self, detail:dict, indicator_score_data:dict):
        self.name = detail["Metadata"]["Category"]
        self.code = detail["Metadata"]["CategoryCode"]
        self.indicators = []
        self.load(detail, indicator_score_data)

    def __repr__(self):
        return f"Category<{self.code}: {self.score()}; {self.indicators}"

    def __str__(self):
        return f"Category<{self.code}: {self.score()}; {self.indicators}"

    def score(self):
        return sum([indicator.score for indicator in self.indicators])/len(self.indicators)

    def load(self, detail:dict, indicator_score_data:dict):
        """
        When called the first time (from the constructor) it loads the first indicator from the detail.
        Successive calls load additional indicator
        """
        matched_indicator = self.get_indicator(detail["Metadata"]["IndicatorCode"])
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
            self.name = detail["Metadata"]["Indicator"]
            self.code = detail["Metadata"]["IndicatorCode"]
        except KeyError as ke:
            raise InvalidDocumentFormatError(f"Indicator Detail Missing Name or Indicator Code {detail} ({ke})")
        try:
            self.score = indicator_score_data["Score"]
        except KeyError as ke:
            raise InvalidDocumentFormatError(f"Indicator Data Missing 'Score' ({indicator_score_data})")
        if self.code != indicator_score_data["IndicatorCode"]:
            raise DataOrderError(f"Mismatched Data and Indicator Detail {detail}; {indicator_score_data}")
        if type(self.score) is float:
            if self.score < 0 or self.score > 1:
                raise InvalidDocumentFormatError(f"Score is not between 0 and 1! ({self})")
