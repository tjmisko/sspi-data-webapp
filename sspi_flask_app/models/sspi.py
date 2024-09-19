class SSPI:
    def __init__(self, indicator_details:list, country_scores:list):
        """
        indicator_details - Expects a list of dictionaries in Metadata format (see sspi_metadata)
        country_scores - Expects a list of dictionaries of scores for a given country
        - [ ] To-do @tjmisko: set up to handle years, maybe with an SSPIDynamic Object with SSPI objects
        """
        self._indicator_details = indicator_details
        self._indicator_scores = indicator_scores
        self.pillars = self.load_structure(self._indicator_details, self._indicator_scores)
        self.categories = [p.categories for p in self.pillars]
        self.indicators = [c.indicators for c in self.categories]

    def score(self):
        return sum([pillar.score() for pillar in self.pillars])/len(self.pillars)
    
    def score_tree(self):
        # return sum([pillar.score() for pillar in self.pillars])/len(self.pillars)
        pass

    def pillar_scores(self):
        return {pillar.code: pillar.score() for pillar in self.pillars}

    def extract_score(self, IndicatorCode:str, indicator_scores:list):
        for indicator in indicator_scores:
            if indicator["IndicatorCode"] == IndicatorCode:
                return indicator["Score"]
        return None

    def load_structure(indicator_details, indicator_scores):
        for detail in indicator_details:
            indicator_score = self.extract_score(detail["Metadata"]["IndicatorCode"], indicator_scores)
            matched_pillar = self.get_pillar(detail["Metadata"]["PillarCode"])
            if not matched_pillar:
                matched_pillar = Pillar(detail, indicator_score)
                self.pillars.append(matched_pillar)
            matched_pillar.load_structure(detail, indicator_score)

    def get_pillar(self, PillarCode):
        """
        Takes in a PillarCode and returns the matching pillar object.
        Returns None if no match exists
        """
        for pillar in self.pillars:
            if PillarCode == pillar.code:
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
    def __init__(self, detail, indicator_score):
        self.name = detail["Metadata"]["Pillar"]
        self.code = detail["Metadata"]["PillarCode"]
        self.categories = self.load_structure(detail, indicator_score)

    def score(self):
        return sum([category.score() for category in self.categories])/len(self.categories)
    
    def load_structure(self, detail):
        """
            When called the first time (from the constructor) it loads the first category from the detail.
            Successive calls load additional categories
        """
        matched_category = self.get_category(detail["Metadata"]["CategoryCode"])
        if not matched_category:
            matched_category = Category(detail)
            self.categories.append(matched_category)
        matched_category.load_structure(detail)

    def get_category(self):
        for category in self.categories:
            if PillarCode == category.code:
                return category
            return None

class Category:
    def __init__(self, detail:dict, indicator_score_data:dict):
        self.name = detail["Metadata"]["Category"]
        self.code = detail["Metadata"]["CategoryCode"]
        self.indicators = []
        self.load_structure(detail, indicator_score_data)

    def score(self):
        return sum([indicator.score for indicator in self.indicators])/len(self.indicators)

    def load_structure(self, detail:dict, indicator_score_data:dict):
        """
            When called the first time (from the constructor) it loads the first category from the detail.
            Successive calls load additional categories
        """
        matched_indicator = self.get_indicator(detail["Metadata"]["CategoryCode"])
        if matched_indicator:
            matched_indicator.load_structure(detail, indicator_score_data)
        else:
            new_indicator = Indicator(detail, indicator_score_data)
            self.indicators.append(new_indicator)

    def get_indicator(self, indicator_code):
        for indicator in self.indicators:
            if indicator_code == indicator.code:
                return indicator
            return None

class Indicator:
    def __init__(self, detail, indicator_score_data):
        self.code = detail["Metadata"]["IndicatorCode"]
        self.score = indicator_score_data["Score"]

    def load_structure(self, detail, indicator_score_data):
        self.code = detail["Metadata"]["IndicatorCode"]
        self.score = indicator_score["Score"]
