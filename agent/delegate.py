class Delegate:
    def __init__(self, id, name, level="beginner"):
        self.id = id
        self.name = name
        self.level = level # TODO: choose level with numbers ?
        self.score = 0
        self.history = []  

    def update_score(self, value):
        # TODO: make this function more logical.
        self.score += value

    def add_interaction(self, doctor_feedback):
        self.history.append(doctor_feedback)

    def get_profile(self):
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "score": self.score
        }

    def level_up(self):
        # TODO: make this function more logical.
        if self.score >= 50:
            self.level = "intermediate"
        if self.score >= 100:
            self.level = "expert"

    def __str__(self):
        return f"Delegate {self.name} (Level: {self.level}, Score: {self.score})"