class Team:
    def __init__(self, name, player_indices):
        self.name = name
        self.player_indices = tuple(player_indices)
        self.score = 0
        self.bags = 0

    def reset_game(self):
        self.score = 0
        self.bags = 0
