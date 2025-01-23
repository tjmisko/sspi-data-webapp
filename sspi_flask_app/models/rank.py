class EquivalenceClass:
    def __init__(self, equivalence_value: float, tol=1E-8):
        self.value = equivalence_value
        self.tol = tol
        self.data = []

    def test(self, value) -> bool:
        return abs(value - self.value) < self.tol

    def add(self, obs: dict):
        self.data.append(obs)

    def rank(self, rank: int):
        for obs in self.data:
            obs["Rank"] = rank


class SSPIRankingTable:
    def __init__(self, data: list[dict]):
        self.data = data
        self.classes = []
        self.rank_by_value = all([
            all(["Value" in obs.keys() for obs in data]),
            all(["LowerGoalpost" in obs.keys() for obs in data]),
            all(["UpperGoalpost" in obs.keys() for obs in data])
        ])
        if self.rank_by_value:
            self.inverted = self.detect_inversion()
            self.assign_classes("Value")
        else:
            self.inverted = False
            self.assign_classes("Score")
        self.compute_ranks()

    def assign_classes(self, key):
        for obs in self.data:
            value = float(obs[key])
            matched_class = None
            for cls in self.classes:
                if cls.test(value):
                    matched_class = cls
                    break
            if not matched_class:
                matched_class = EquivalenceClass(value)
                self.classes.append(matched_class)
            matched_class.add(obs)

    def compute_ranks(self):
        self.classes.sort(key=lambda cls: -cls.value, reverse=self.inverted)
        r = 1
        for i, cls in enumerate(self.classes):
            # When tied for last, the ranking should be last (e.g. 49
            # in the 2018 SSPI)
            if i + 1 == len(self.classes):
                cls.rank(len(self.data))
            else:
                cls.rank(r)
            r += len(cls.data)

    def validate_goalposts(self):
        if self.rank_by_value:
            ref_lg = self.data[0]["LowerGoalpost"]
            ref_ug = self.data[0]["UpperGoalpost"]
            for obs in self.data[1:]:
                if abs(obs["LowerGoalpost"] - ref_lg) > 1E-5:
                    message = "Mismatched Lower Goalposts " + \
                        str(ref_lg) + " and " + str(obs["LowerGoalpost"])
                    raise ValueError(message)
                if abs(obs["UpperGoalpost"] - ref_ug) > 1E-5:
                    message = "Mismatched Upper Goalposts " + \
                        str(ref_ug) + " and " + str(obs["UpperGoalpost"])
                    raise ValueError(message)

    def detect_inversion(self):
        self.validate_goalposts()
        return self.data[0]["LowerGoalpost"] > self.data[0]["UpperGoalpost"]
