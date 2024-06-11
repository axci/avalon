import gymnasium as gym
from gymnasium import spaces
from pydantic import BaseModel
from typing import  ClassVar, Dict, List, Tuple
import numpy as np
from itertools import combinations, permutations

class AvalonGameSetup(BaseModel):
    """
    AvalonGameSetup class for setting up the game Avalon based on the number of players.

    CONFIG: 
        A dictionary where the key is the number of players, and the value is a list of three lists:
            (1) contains the number of good and evil players.
            (2) contains the number of players required for each quest.
            (3) contains the number of fails required for each quest.

    Attributes:
        num_players (int): Number of players in the game.
        num_good (int): Number of good players.
        num_evil (int): Number of evil players.
        num_players_for_quest (List[int]): Number of players required for each quest.
        num_fails_for_quest (List[int]): Number of fails required for each quest.

    Class Variables:
        PHASES (Dict[int, str]): A dictionary of game phases.
        ROLES (Dict[int, str]): A dictionary of player roles.
        MAX_ROUNDS (int): Maximum number of rounds in the game.

    Methods:
        from_num_players(cls, num_players: int) -> 'AvalonGameSetup':
            Class method to instantiate the class from the number of players.
    
    """
    CONFIG: ClassVar[Dict[int, List[List[int]]]]  =   {
            5 :  [[3, 2] , [2, 3, 2, 3, 3], [1, 1, 1, 1, 1],], 
            6 :  [[4, 2] , [2, 3, 4, 3, 4], [1, 1, 1, 1, 1],], 
            7 :  [[4, 3] , [2, 3, 3, 4, 4], [1, 1, 1, 2, 1],], 
            8 :  [[5, 3] , [3, 4, 4, 5, 5], [1, 1, 1, 2, 1],], 
            9 :  [[6, 3] , [3, 4, 4, 5, 5], [1, 1, 1, 2, 1],], 
            10 : [[6, 4] , [3, 4, 4, 5, 5], [1, 1, 1, 2, 1],],
         }
    
    num_players: int
    num_good: int
    num_evil: int
    num_players_for_quest: List
    num_fails_for_quest: List
    
    PHASES: ClassVar[Dict[int, str]] = {
        0 : "Team Building", 
        1 : "Team Voting", 
        2 : "Quest Voting", 
        3 : "Assassination",
    }
    
    ROLES: ClassVar[Dict[int, str]]  = {
        0 : "Servant", 
        1 : "Merlin", 
        2 : "Minion", 
        3 : "Assassin", 
    }
    
    MAX_ROUNDS: ClassVar[int] = 5  # maximum number of rounds
    
    @classmethod  # it receives the class itself as the first argument, instead of an instance
    def from_num_players(cls, num_players: int) -> 'AvalonGameSetup':
        try:
            if num_players not in cls.CONFIG:
                raise ValueError(f"Invalid number of players: {num_players}. Valid numbers are {list(cls.CONFIG.keys())}.")
            num_good = cls.CONFIG[num_players][0][0]
            num_evil = cls.CONFIG[num_players][0][1]
            num_players_for_quest: List[int] = cls.CONFIG[num_players][1]
            num_fails_for_quest: List[int] = cls.CONFIG[num_players][2]
            return cls(
                num_players=num_players,
                num_good=num_good,
                num_evil=num_evil,
                num_players_for_quest=num_players_for_quest,
                num_fails_for_quest=num_fails_for_quest,
            )
        except KeyError as e:
            raise ValueError(f"Invalid configuration for {num_players} players.") from e
        except Exception as e:
            raise ValueError(f"An error occurred: {e}") from e
    
class AvalonGameEnv(gym.Env):
    # metadata = []
    
    def __init__(self, setup: AvalonGameSetup, render_mode=None):
        """
        action_space: {
            phase 0: all possible combinations for team selection 
            phase 1: 
            phase 2,
            phase 3,              
        }
            
        """
        
        self.setup = setup        
        # this will give me self.num_players, self.num_good, ... from AvalonGameSetup
        for key, value in setup.dict().items():
            setattr(self, key, value)  
        
        self.render_mode = render_mode

        self.observation_space = spaces.Dict({
            "num_players": spaces.Discrete(6, start=5),   # from 5 to 10
            "round": spaces.Discrete(5),         # from 0 to 4
            "phase": spaces.Discrete(4),         # from 0 to 3 
            "quest_leader": spaces.Discrete(self.num_players)  # Leader is one of the players
        })

        # Generate all possible combinations for team selection. 
        # In the last round ([-1]) there are the maximum number of team members.
        #max_number_team_members = self.num_players_for_quest[-1]
        #self.team_combinations = list(combinations(range(self.num_players), max_number_team_members))
        #self.team_voting_combinations = list(product([0, 1], repeat=self.num_players))
        #self.quest_voting_combinations = list(product([0, 1], repeat=max_number_team_members))

        self.action_space = None  # ??????
        
    def _get_obs(self):
        return {
            "num_players": self.num_players,
            "round": self.round,
            "phase": self.phase, 
            "quest_leader": self.leader,
        }
    
    def _get_info(self):
        return {
            "num_players": self.num_players,
            "round": self.round,
            "phase": self.phase,
            "good_victory": self.good_victory,
        }
    
    def reset(self, seed=None, options=None):
        """ Reset game environment. """
        super().reset(seed=seed)  # We need the following line to seed self.np_random
        
        self.round = 0  # there are 5 rounds: 0, 1, 2, 3 , 4 
        self.voting_attempt = 0 
        self.phase = 0  # there 4 phases 0, 1, 2, 3
        self.done = False
        self.good_victory = False
        self.quest_results = []
        self.quest_team = []
        self.team_votes = []
        self.quest_votes = []
        
        # Randomly choose a leader 
        self.leader: int = self.np_random.integers(0, self.num_players, dtype=int)
        observation = self._get_obs()
        info = self._get_info()
        self.roles = self.assign_roles()
        return observation, info
    
    def assign_roles(self) -> List:
        """
        Randomly assign ROLES to the players
        """
        # init
        self.roles = np.full(self.num_players, 0)
        self.is_good = np.full(self.num_players, True)
        
        evil_players: np.array = np.random.choice(self.num_players, self.num_evil, replace=False)  # array(1, 4) players with ids 1 and 4 are evil
        
        self.is_good[evil_players] = False
        good_players = np.where(self.is_good)[0]
        
        # create evil roles (3: assassin (unique), 2: minion (all the others) )
        evil_roles: List = [3] + [2] * (self.num_evil - 1)  # [3, 2, 2] if there are 3 evil characters
        
        # randomly assign evil roles
        self.roles[evil_players] = np.random.choice(evil_roles, self.num_evil, replace=False)
        
        # create good roles: 1: merlin (unique), 0: servant (all the others) 
        good_roles: List = [1] + [0] * (self.num_good - 1) # [1, 0, 0] if there are 3 good characters
        self.roles[good_players] = np.random.choice(good_roles, self.num_good, replace=False)
        
        return self.roles # [self.setup.ROLES[role] for role in self.roles]
    
    def get_role(self, player: int) -> Tuple[int, str, bool]:
        """
        Given a player's id returns:
            (player's role id, role name, whether role is good)
        """
        role_id = self.roles[player]
        role_name = self.setup.ROLES[role_id]
        role_is_good = self.is_good[player]
        return (role_id, role_name, role_is_good)
    
    def get_roles(self) -> List[Tuple[int, str, bool]]:
        """
        Returns a list of tuples (player's role id, role name, whether role is good)
        """
        return [(role, self.setup.ROLES[role], self.is_good[player]) for player, role in enumerate(self.roles)]

    def get_knowledge(self, player: int) -> List:
        """
        Given a player's id returns:
            []
        """
        # if player is evil or Merlin, he/she knows others roles
        if not self.is_good[player] or self.roles[player] == 1:
            return self.is_good
        else:  # -1 for unknow roles (only 1 for yourself)
            return [-1 if p != player else 1 for p in range(self.num_players)]
        
    def get_phase(self) -> Tuple[int, str]:
        """ Returns a tuple (phase index, phase name) """
        return (self.phase, self.setup.PHASES[self.phase])
    
    def get_team_size(self) -> int:
        """ Return the size of the team according to the game round """
        return self.num_players_for_quest[self.round]
    
    def get_combinations_for_servant(self, player: int) -> List:
        """
        Given Servant player id, 
        get all possible combinations of Evil/Good for the Servant.
        """
        elements = [0] * self.num_evil + [1] * (self.num_good - 1)  # not including yourself
        
        # Generate all permutations
        all_permutations = list(permutations(elements))

        # Remove duplicate permutations by converting the list to a set, then back to a list
        unique_permutations = list(set(all_permutations))
        possible_combinations = [list(perm) for perm in unique_permutations]  ##Create a list of lists

        # Insert youself as Good (1)
        for perm in possible_combinations:
            perm.insert(player, 1)

        return possible_combinations

    def get_team_combinations(self) -> List:
        team_combinations = list(combinations(range(self.num_players), self.get_team_size()))
        return team_combinations
    
    def get_team_good_combinations(self) -> List:
        """ 
        Get all possible combinations with Good players
        """
        team_combinations = list(combinations(np.where(self.is_good)[0], self.get_team_size()))
        return team_combinations
    
    def choose_quest_team(self, team: List, leader: int, verbose=False):
        """ 
        ========== PHASE 0 =============
        Input:
            team: a list of players_id chosen by the leader
        
        self.quest_team now equals to the chosen team.
        
        Returns:            
        
        """
        
        assert len(team) == self.num_players_for_quest[self.round], f"The team size for the round #{self.round+1} should be {self.num_players_for_quest[self.round]}."
        assert len(team) == len(set(team)), "All players in the list must be unique." 
        assert self.phase == 0, f"The game must be in the phase 0 (Team Building), but the game now is in the phase {self.get_phase()}."
        assert leader == self.leader, f"The leader should be the player #{self.leader}."
        
        self.quest_team = team  
        
        self.phase += 1  # move to the next phase - Voting
        self.leader = (leader + 1) % self.num_players  # change the leader
        if verbose:
            print(f"ROUND #{self.round + 1}. Phase: (0, Team Building):")
            print(f'Leader: player #{leader}. Chosen Team: {self.quest_team})')
            print(f"The next Leader: player #{self.leader}")
            print("=========================================")
        return (self.phase, self.done, self.leader)
    
    def gather_team_votes(self, votes: List, verbose=False) -> Tuple[int, bool, bool]:
        """
        ========== PHASE 1 =============
        votes: List of 0 and 1, where 0 - rejected, 1 - accepted
            Example:
                votes = [0, 1, 1, 1, 1]  # every player votes
        Returns:
            (next phase, whether the game is done, whether team is accepted)
            Example:
                (0, False, False)  # we're in the same PHASE, because the TEAM wasn't accepted
        """
        assert len(votes) == self.num_players, f"Number of votes ({len(votes)}) does not match the number of players ({self.num_players})."
        assert self.phase == 1, f"The game is in the {self.get_phase()} phase. It should be in the Voting Phase."
        
        self.team_votes = votes
        
        # strict majority?        
        if sum(votes) > self.num_players / 2:
            self.phase += 1  # move to the next phase
            self.voting_attempt = 0  # reset voting attempts
            if verbose:
                print(f"ROUND #{self.round + 1}. Phase: (1, Team Voting):")
                print(f'Success. ({sum(votes)} out of {self.num_players}) voted for the Team.')
                print(f'The next Phase: {self.get_phase()}')
                print("=========================================")
            return (self.phase, self.done, True)
        else:
            self.phase = 0
            self.voting_attempt += 1
            if verbose:
                print(f"ROUND #{self.round + 1}. Phase: (1, Team Voting):")
                print(f'Fail. {sum(votes)} out of {self.num_players} players voted for the Team (should be majority).')
                print(f"The total number of failed elections in this Round: {self.voting_attempt}.")
                print(f'The next Phase: {self.get_phase()}.')
                print("=========================================")
            
            # Evil wins the game if 5 teams are rejected in a single round 
            if self.voting_attempt == self.setup.MAX_ROUNDS:
                self.done = True  # XXXXXXXXXXX END OF THE GAME XXXXXXXXXXXX
                self.good_victory = False
                self.phase = 1
                if verbose:
                    print(f'== The end ==. 5 consecutive failed Votes. Evil wins 😈 ')
            return (self.phase, self.done, False)     
        
    def gather_quest_votes(self, votes: List[int], verbose=False) -> Tuple[int, bool, bool, int]:
        """
        ========== PHASE 2 =============
        votes: List, 0 for fail, 1 for success
        Returns:
            (next phase, whether the game is done, whether the quest succeeded, 
             number of fails in this round)
        """
        assert self.phase == 2, f"The game must be in the phase 2 (Quest Voting), but the game now is in the phase {self.get_phase()}."
        assert len(votes) == self.num_players_for_quest[self.round], f"The number of votes ({len(votes)}) does not equal to the team size ({self.num_players_for_quest[self.round]}). It must be equal."
        
        self.quest_votes = votes
        
        votes_to_fail: int = self.num_fails_for_quest[self.round] # 1 or 2
        num_fails: int = len(votes) - sum(votes)  # how many players voted to fail the mission in this round
        
        if num_fails >= votes_to_fail:
            # fail
            self.quest_results.append(False) # save history
            
            # count number of fails
            total_num_fails = len(self.quest_results) - sum(self.quest_results)
            # after 3 fails Evil wins
            if total_num_fails == 3:
                self.done = True  # XXXXXXXX END OF THE GAME XXXXXXXXXXXX
                self.good_victory = False
                if verbose:
                    print(f"ROUND #{self.round + 1}. Phase: (2, Quest Voting)")
                    print(f'Quest Team: {self.quest_team}')
                    print(f"Quest failed. {num_fails} player(s) voted to Fail.")
                    print(f'== The end. 3 failed Quests. Evil wins 😈 ')
                    print("=========================================")
            else:
                if self.round != 4:
                    self.round += 1
                    self.phase = 0
                if verbose:
                    print(f"ROUND #{self.round}. Phase: (2, Quest Voting)")
                    print(f'Quest Team: {self.quest_team}')
                    print(f"Quest failed. {num_fails} player(s) voted to Fail. ")
                    print(f"Total number of failed Quests: {total_num_fails}.")
                    print(f"The next Round: {self.round + 1}. The next Phase: {self.get_phase()}")
                    print("=========================================")
            return (self.phase, self.done, False, num_fails)
        
        else: # SUCCESS
            self.quest_results.append(True)
            
            # 3 successes?
            if sum(self.quest_results) == 3:
                self.phase += 1 # go to the assassination phase
            else:
                if self.round !=4:
                    self.round += 1
                    self.phase = 0
            if verbose:
                    total_num_fails = len(self.quest_results) - sum(self.quest_results)
                    print(f"ROUND #{self.round + 1}. Phase: (2, Quest Voting):")
                    print(f'Quest Team: {self.quest_team}')
                    print(f"Quest succeeded. {num_fails} player(s) voted to Fail.")
                    print(f"Total number of failed Quests: {total_num_fails}.")
                    print(f"The next Round: {self.round + 1}. The next Phase: {self.get_phase()}")
                    print("=========================================")
            
            return (self.phase, self.done, True, num_fails)
        
    def choose_assassin_target(self, player: int, target: int, verbose=False) -> Tuple:
        """
        ========== PHASE 3 =============
        Return:
            (next phase, whether the game is done, whether Good wins)
        """
        assert self.phase == 3, f"The game must be in the phase 3 (Assassination), but the game now is in the phase {self.get_phase()}."
        assert self.roles[player] == 3, "The player is not Assassin."
        assert self.is_good[player] == False, f"Assassin can not be good."
        
        self.done = True  # XXXXXXXX END OF THE GAME XXXXXXXXXXXX
        
        # Assassination
        if self.roles[target] == 1:  # if the Target is Merlin, Evil wins
            self.good_victory = False
        else:
            self.good_victory = True
        
        if verbose:
            print(f"ROUND #{self.round + 1}. Phase: (3, Assassination)")
            print(f"Assassin chooses the player #{target} ({self.get_role(target)}) as a target.")
            if self.good_victory:
                print(f"== The End. Good wins!")
            else:
                print(f"== The End. Evil wins 😈 ")
        return (self.phase, self.done, self.good_victory)
    
    def step(self, action, verbose=False):
        ##### PHASE 0: TEAM BUILDING #####
        ##### Decision maker: Leader #####
        if self.phase == 0:
            team = action
            self.choose_quest_team(team, self.leader, verbose=verbose)         

        elif self.phase == 1:
            votes = action
            self.gather_team_votes(votes, verbose=verbose)

        elif self.phase == 2:
            votes = action
            self.gather_quest_votes(votes, verbose=verbose)

        elif self.phase == 3:
            target = action
            player = np.where(self.roles==3)[0][0]  # index of assassin player
            self.choose_assassin_target(player, target, verbose=verbose)

        observation = self._get_obs()
        info = self._get_info()
        reward = None
        return observation, reward, self.done, False, info
        

def simulate_game(num_players=5, verbose=False):
    print('== GAME BEGINS ==')
    setup = AvalonGameSetup.from_num_players(num_players)
    env = AvalonGameEnv(setup)
    env.reset()
    leader = env.leader
    
    while not env.done:
        # PHASE 0
        team = np.random.choice(range(num_players), size=env.num_players_for_quest[env.round], replace=False).tolist()
        phase, done, leader = env.choose_quest_team(team, leader, verbose=verbose)
        
        # PHASE 1
        votes = np.random.choice([0, 1], size=num_players, replace=True)
        next_phase, done, team_is_accepted = env.gather_team_votes(votes, verbose=verbose)
        
        if next_phase == 2:
            # PHASE 2
            votes_quest = np.random.choice([0, 1], size=env.num_players_for_quest[env.round], replace=True, p=[0.2, 0.8])
            next_phase, done, quest_is_succeded, fails_num = env.gather_quest_votes(votes_quest, verbose=verbose)

        if next_phase == 3:
            player = np.where(env.roles==3)[0][0]  # index of assassin player
            good_players = np.where(env.is_good)[0]
            target = np.random.choice(good_players)
            env.choose_assassin_target(player, target, verbose=verbose)
    return env.good_victory