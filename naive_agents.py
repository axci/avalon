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
        self.possible_combinations = self.env.get_combinations_for_servant(player)
        self.probabilities_good = np.array(self.possible_combinations).sum(axis=0) / len(self.possible_combinations)
    
    def __repr__(self):
        return f"NaiveServant(player #{self.player}, role={self.role}"
        
    def get_team_with_hightest_probability(self):
        """
        1. All possible combinations of players, for example (G, E, G, G, E)

        Returns:
            a list of teams with the highest probabilities to be Good
        """
        team_combinations = self.env.get_team_combinations()  # all possible team combinations

        # Calculate the probability for each team combination
        team_combinations_probabilities = []
        for team_combination in team_combinations:
            probability = 1
            for player in team_combination:
                probability *= self.probabilities_good[player]
            team_combinations_probabilities.append(probability)

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
        if not self.env.done:        
            if verbose:
                print(f"+++++ Updating Believes for player #{self.player}")
            
            # Updating believes
            # Assumes that all Good vote 1, all Evil vote 0
            #print(self.env.quest_team)
            #print(self.env.quest_votes)

            accepted_votes = sum(self.env.quest_votes)

            # Assumes that all Good vote 1, all Evil vote 0
            pos_combinations_strict = [comb for comb in self.possible_combinations if sum( comb[member] for member in self.env.quest_team ) == accepted_votes ]
            #print("strict combinations:", pos_combinations_strict)
            #print(pos_combinations_strict == True)
            # But Evil can vote 1 also. You can't get empty list of combinations
            if pos_combinations_strict:  # if list is not empty
                self.possible_combinations = pos_combinations_strict
            
            self.probabilities_good = np.array(self.possible_combinations).sum(axis=0) / len(self.possible_combinations)
            #print(self.possible_combinations)
            #print(self.probabilities_good)

            if verbose:
                print(f'Player #{self.player}.')
                print(f'Possible combinations : {self.possible_combinations}')
                print(f'Probabilities to be Good: {self.probabilities_good }')
    

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