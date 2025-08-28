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

    def label_tie(self):
        for obs in self.data:
            obs["Tie"] = len(self.data) > 1


class SSPIRankingTable:
    def __init__(self, data: list[dict]):
        self.data = data
        self.classes = []
        self.inverted = False
        self.assign_classes("Score")
        self.compute_ranks()
        self.label_ties()

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
            cls.rank(r)
            r += len(cls.data)


    def label_ties(self):
        for cls in self.classes:
            cls.label_tie()
