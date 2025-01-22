class EquivalenceClass:
    def __init__(self, equivalence_value: float, tol=1E-8):
        self.value = equivalence_value
        self.tol = tol
        self.data = []

    def test(self, value) -> bool:
        return abs(value - self.value) < self.tol

    def add(self, value):
        self.data.append(value)

    def rank(self, rank):
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
            self.assign_classes("Value")
        else:
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
            matched_class.add(value)

    def compute_ranks(self):
        self.classes.sort(key=lambda cls: cls.value)
        r = 1
        for i, cls in enumerate(self.classes):
            if i + 1 == len(self.classes):
                cls.rank(len(self.data))
            cls.rank(r)
            r += len(cls.data)
