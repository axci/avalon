import numpy as np
import random


class RandomBot:
    """
    Agent chooses actions absolutely randomly
    """
    def __repr__(self):
        return f"RandomBot(player #{self.player}, role={self.role}"
    
    def __init__(self, env, player: int):
        self.env = env
        self.player = player
        self.role = env.get_role(player)
        
    def play(self, verbose=False):
        if self.env.phase == 0 and self.env.leader == self.player:
            action = np.random.choice(range(self.env.num_players), 
                                      size=self.env.num_players_for_quest[self.env.round], 
                                      replace=False
                                     ).tolist()
            return action
        
        elif self.env.phase == 1:
            # Vote for the Team
            action = np.random.choice([0, 1])
            return action
        
        # If you are in the team
        elif self.env.phase == 2 and self.player in self.env.quest_team:
            action = np.random.choice([0, 1])
            return action
        
        elif self.env.phase == 3 and self.env.roles[self.player] == 3: # if I am an assassin
            good_players = np.where(self.env.is_good)[0]
            if verbose:
                print(f'GOOD PLAYERS: {good_players}')
            action = np.random.choice(good_players)
            return action
        
class NaiveMinion:
    def __init__(self, env, player: int):
        self.env = env
        self.player = player
        self.role = env.get_role(player)
        
    def __repr__(self):
        return f"NaiveMinion(player #{self.player}, role={self.role}"
        
    def play(self, verbose=False):
        ######### PHASE 0 ##########
        if self.env.phase == 0 and self.env.leader == self.player:
            team = [self.player] # always chooses itself,
            
            #choose others randomly
            players_to_choose_from = [player for player in range(self.env.num_players) if player != self.player]
            others = np.random.choice(players_to_choose_from, size=self.env.get_team_size() - 1, replace=False)
            team += list(others)
            if verbose:
                print("I am MINION. And I am Leader.")
                print(f"I choose the following team: {team}")
            return team
        
        ######### PHASE 1 ##########
        elif self.env.phase == 1:            
            # If at leaset 1 Evil player in Team
            if False in self.env.is_good[list(self.env.quest_team)]:
                if verbose:
                    print(f"Team (self.env.quest_team) has at least 1 Evil player.")
                    print('Accepted!')
                return 1
            else:
                if verbose:
                    print(f"Team (self.env.quest_team) doesn't have Evil players.")
                    print('Rejected!')
                return 0

        ######### PHASE 2 ##########
        elif self.env.phase == 2 and self.player in self.env.quest_team:
            # if Assassin in Team - Fail
            if 3 in self.env.roles[list(self.env.quest_team)]:
                if verbose:
                    print(f'Assassin (player #{np.where(self.env.roles==3)[0][0] }) is in the Quest Team. Support Mission.')
                return 1
            else:
                if verbose:
                    print(f'There is no Assassin in Quest Team. Fail Mission.')
                return 0

class NaiveAssassin(NaiveMinion):
    def __repr__(self):
        return f"NaiveAssassin(player #{self.player}, role={self.role}"
    
    def play(self, verbose=False):
        ######### PHASE 0 ##########
        if self.env.phase == 0 and self.env.leader == self.player:
            
            team = [self.player] # always chooses itself,
            
            #choose others randomly
            players_to_choose_from = [player for player in range(self.env.num_players) if player != self.player]
            others = np.random.choice(players_to_choose_from, size=self.env.get_team_size() - 1, replace=False)
            team += list(others)
            if verbose:
                print("I am ASSASSIN. And I am Leader.")
                print(f"I choose the following team: {team}")
            return team
        
        ######### PHASE 1 ##########
        elif self.env.phase == 1:            
            # If at leaset 1 Evil player in Team
            if False in self.env.is_good[list(self.env.quest_team)]:
                if verbose:
                    print(f"Team (self.env.quest_team) has at least 1 Evil player.")
                    print('Accepted!')
                return 1
            else:
                if verbose:
                    print(f"Team (self.env.quest_team) doesn't have Evil players.")
                    print('Rejected!')
                return 0

        ######### PHASE 2 ##########
        elif self.env.phase == 2 and self.player in self.env.quest_team:
            # Assassin will always choose FAIL
            if verbose:
                print('I am Assassin. I fail the mission (as alwayes).')
            return 0
        
        ######### PHASE 3 ##########
        elif self.env.phase == 3:
            good_players = np.where(self.env.is_good)[0]
            action = np.random.choice(good_players)
            if verbose:
                print(f'GOOD PLAYERS: {good_players}')

            return action
        
class NaiveServant:
    def __init__(self, env, player: int):
        self.env = env
        self.player = player
        self.role = env.get_role(player)
        self.probabilities_good = [(self.env.num_good - 1) / (self.env.num_players - 1) for _ in range(self.env.num_players)]
        self.probabilities_good[self.player] = 1
        #self.believes = {combination: 0 for combination in self.env.get_team_combinations()}
        self.exclude_combinations = []
    
    def __repr__(self):
        return f"NaiveServant(player #{self.player}, role={self.role}"
    
    # Function to check if a tuple is part of any exclude set
    def _is_excluded(self, combo, exclude_sets):
        combo_set = set(combo)
        for ex_set in exclude_sets:
            if combo_set.issubset(ex_set):
                return True
        return False
    
    
    def get_team_with_hightest_probability(self):
        """
        Returns:
            a list of teams with the highest probabilities to be Good
        """
        team_combinations = self.env.get_team_combinations()  # all possible team combinations
        
        # Calculate the probability for each team combination
        team_combinations_probabilities = []
        for team_combination in team_combinations:
            if not self._is_excluded(team_combination, self.exclude_combinations):  # if the team comb is not in excluded
                probability = 1
                for player in team_combination:
                    probability *= self.probabilities_good[player]
                team_combinations_probabilities.append(probability)
            else:
                team_combinations_probabilities.append(0)

        highest_probability = max(team_combinations_probabilities)
        
        # Filter team combinations with the highest probability
        teams_with_highest_probability = [
            team for team, prob in zip(team_combinations, team_combinations_probabilities)
            if prob == highest_probability
        ]

        return teams_with_highest_probability
    
    
    def play(self, verbose=False):
        """
        PHASE 0. 
        """

        ######### PHASE 0 ##########
        teams_with_hightest_probability = self.get_team_with_hightest_probability()
        team = random.choice(teams_with_hightest_probability)
        if self.env.phase == 0 and self.env.leader == self.player:
            if verbose:
                print("I am NAIVE SERVANT. I am Leader.")
                print(f"I choose the team: {team}")
            return team
        
        ######### PHASE 1 ##########
        elif self.env.phase == 1:
            if self.env.voting_attempt == 4:
                return 1  # You have to accept otherwise you will loose
            elif self.env.quest_team in teams_with_hightest_probability:
                if verbose:
                    print(f"Team (self.env.quest_team) has the hightest probability to be Good")
                    print('Accepted!')
                return 1
            else:
                if verbose:
                    print(f"Team (self.env.quest_team) has NOT the hightest probability to be Good")
                    print('Rejected!')
                return 0
        
        ######### PHASE 2 ##########    
        elif self.env.phase == 2 and self.player in self.env.quest_team:
            return 1
        
    def update_believes(self, verbose=False):        
        if verbose:
            print(f"+++++ Updating Believes for player #{self.player}")
        
        # Updating believes
        evil_containing_combination = []
        # If I am in the Quest Team
        if self.player in self.env.quest_team:
            if sum(self.env.quest_votes) <= 1: # only I voted for the Success => all other players are Evil
                for member in self.env.quest_team:
                    if member != self.player:
                        self.probabilities_good[member] = 0
                        if verbose:
                            print(f"Belief: Player #{member} is Evil.")
            elif sum(self.env.quest_votes)  == len(self.env.quest_votes): # all the players voted 1
                for member in self.env.quest_team:
                    self.probabilities_good[member] = 1
                    if verbose:
                        print(f"Belief: Player #{member} is Good.")
            else:
                #evil_containing_combination = []
                for member in self.env.quest_team:
                    if member != self.player:
                        evil_containing_combination.append(member)
             
        # If I am not in the Quest Team
        else:
            if sum(self.env.quest_votes) == 0:
                for member in self.env.quest_team:
                    self.probabilities_good[member] = 0
                    if verbose:
                        print(f"Belief: Player #{member} is Evil.")
            elif sum(self.env.quest_votes)  == len(self.env.quest_votes): # all the players voted 1
                for member in self.env.quest_team:
                    self.probabilities_good[member] = 1
                    if verbose:
                        print(f"Belief: Player #{member} is Good.")
            else:
                #evil_containing_combination = []
                for member in self.env.quest_team:
                    evil_containing_combination.append(member)
        
        # update my believes: I will never choose a Team with this combination
        if evil_containing_combination and set(evil_containing_combination) not in self.exclude_combinations: # if there is a combination to exclude
            self.exclude_combinations.append(set(evil_containing_combination))
        if verbose:
            print(f'+++++++ This combination should be ruled out: {evil_containing_combination}')
            print(f'To rule out: {self.exclude_combinations}')

class NaiveMerlin:
    def __init__(self, env, player: int):
        self.env = env
        self.player = player
        self.role = env.get_role(player)
        
    def __repr__(self):
        return f"NaiveMerlin(player #{self.player}, role={self.role}"
        
    def play(self, verbose=False):
        ######### PHASE 0 ##########
        if self.env.phase == 0 and self.env.leader == self.player:
            # Randomly chooses the team with Good players
            good_combinations = self.env.get_team_good_combinations()
            return random.choice(good_combinations)
        
        ######### PHASE 1 ##########
        elif self.env.phase == 1:            
            # If at leaset 1 Evil player in Team
            if False in self.env.is_good[list(self.env.quest_team)]:
                if verbose:
                    print(f"Team (self.env.quest_team) has at least 1 Evil player.")
                    print('Rejected!')
                return 0
            else:
                if verbose:
                    print(f"Team (self.env.quest_team) doesn't have Evil players.")
                    print('Accepted!')
                return 1

        ######### PHASE 2 ##########
        elif self.env.phase == 2 and self.player in self.env.quest_team:
            return 1