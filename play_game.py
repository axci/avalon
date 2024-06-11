from avalon_env import AvalonGameEnv, AvalonGameSetup
from naive_agents import NaiveServant, NaiveMerlin, NaiveMinion, NaiveAssassin
from tqdm import tqdm


def play_game(env, players, verbose=False):

    if verbose:
        print('== GAME BEGINS ==')

    while not env.done:
    ### PHASE 0 ###
    # Who is the leader?
        if env.phase == 0:
            for player in players:
                if player.player == env.leader:
                    action = player.play()
                    _, _, _, _, info = env.step(action, verbose=verbose)
                    if verbose:
                        print(f'Decision Maker: {player}')
                        print("=============================")
                        print("")
                    break

        ### PHASE 1 ###
        elif env.phase == 1:
            votes = []
            for player in players:
                votes.append(player.play())
            _, _, _, _, info = env.step(votes, verbose=verbose)
            if verbose:
                print('Decision Makers:')
                for i, player in enumerate(players):
                    print(f"Player: {player}. Decision: {votes[i]} ")
                print("=============================")
                print("")
                    

        ### PHASE 2 ###
        elif env.phase == 2:
            votes = []
            for player in players:
                if player.player in env.quest_team:
                    votes.append(player.play())
            _, _, _, _, info = env.step(votes, verbose=verbose)
            
            # update Believes for NaiveServant
            naive_servants = [player for player in players if isinstance(player, NaiveServant)]
            for naive_servant in naive_servants:
                naive_servant.update_believes(verbose=verbose)            

            if verbose:
                print('Decision Makers:')
                counter = 0
                for player in players:
                    if player.player in env.quest_team:
                        print(f"Player: {player}. Decision: {votes[counter]} ")
                        counter += 1
                print("=============================")
            
                print("")

        ### PHASE 3 ###
        elif env.phase == 3:
            for player in players:
                if env.roles[player.player] == 3:
                    action = player.play()
                    _, _, _, _, info = env.step(action, verbose=verbose)
                    if verbose:
                        print('========== THE END =============')
                    
    return info


def play_naive_games(n: int, n_players: int):
    """
    Simulate n games.
    """
    stat = {
        "game_id": [],
        "good_victory": [],
        "round": [],
        "phase": [],
        }
    stat_total = {
        "num_players": n_players,
        "good_victory": 0,
        "Round 0": 0,
        "Round 1": 0,
        "Round 2": 0,
        "Round 3": 0,
        "Round 4": 0,
        "Phase 1": 0,
        "Phase 2": 0,
        "Phase 3": 0,
    }

    for game_id in tqdm(range(n)):
        setup = AvalonGameSetup.from_num_players(n_players)
        env = AvalonGameEnv(setup)
        env.reset()

        players = []
        for i, role in enumerate(env.roles):
            if role == 0:
                players.append(NaiveServant(env, player=i))
            elif role == 1:
                players.append(NaiveMerlin(env, player=i))
            elif role == 2:
                players.append(NaiveMinion(env, player=i))
            elif role == 3:
                players.append(NaiveAssassin(env, player=i))
        info = play_game(env, players)
        stat["game_id"].append(game_id + 1)
        stat["good_victory"].append(info["good_victory"])
        stat["round"].append(info["round"])
        stat["phase"].append(info["phase"])

        stat_total["good_victory"] += info["good_victory"]
        if info["round"] == 0:
            stat_total["Round 0"] += 1
        elif info["round"] == 1:
            stat_total["Round 1"] += 1
        elif info["round"] == 2:
            stat_total["Round 2"] += 1
        elif info["round"] == 3:
            stat_total["Round 3"] += 1
        elif info["round"] == 4:
            stat_total["Round 4"] += 1
        if info["phase"] == 1:
            stat_total["Phase 1"] += 1
        if info["phase"] == 2:
            stat_total["Phase 2"] += 1
        if info["phase"] == 3:
            stat_total["Phase 3"] += 1



    return stat, stat_total
