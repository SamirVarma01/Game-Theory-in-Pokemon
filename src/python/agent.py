# Core agent implementation
from poke_env.player.player import Player
from battle_state import BattleStateTracker
from payoff_builder import PayoffMatrixBuilder
from dashboard_connector import DashboardConnector
from data_collector import BattleDataCollector
from opponent_model import OpponentModel
import random
import sys
import os
import logging

# Add absolute path to build directory
build_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../cpp/build'))
if build_path not in sys.path:
    sys.path.insert(0, build_path)

import nash_solver

logger = logging.getLogger(__name__)

class GameTheoryAgent(Player):
    def __init__(self, account_configuration=None, server_configuration=None, battle_format=None, *args, **kwargs):
        super().__init__(
            account_configuration=account_configuration,
            server_configuration=server_configuration,
            battle_format=battle_format,
            *args,
            **kwargs
        )
        self.battle_state_tracker = BattleStateTracker()
        self.opponent_model = OpponentModel()
        self.payoff_builder = PayoffMatrixBuilder(opponent_model=self.opponent_model)
        self.dashboard_connector = DashboardConnector()
        self.data_collector = BattleDataCollector()
        self.last_moves = {}

    def choose_move(self, battle):
        logger.debug(f"=== Starting move selection for battle {battle.battle_tag} ===")
        logger.debug(f"Turn number: {battle.turn}")
        logger.debug(f"Available moves: {[move.id for move in battle.available_moves]}")
        logger.debug(f"Available switches: {[pkmn.species for pkmn in battle.available_switches] if battle.available_switches else []}")
        logger.debug(f"Active Pokemon: {battle.active_pokemon.species if battle.active_pokemon else 'None'}")
        logger.debug(f"Opponent Active Pokemon: {battle.opponent_active_pokemon.species if battle.opponent_active_pokemon else 'None'}")
        
        # Record battle state
        self.data_collector.record_battle_state(
            battle, 
            battle.turn, 
            our_move=self.last_moves.get(battle.battle_tag)
        )
        
        # Force a move selection if we have moves available
        if battle.available_moves:
            logger.debug(f"We have {len(battle.available_moves)} moves available")
            try:
                # Build payoff matrix for available moves
                logger.debug("Building payoff matrix...")
                payoff_matrix = self.payoff_builder.build_matrix(battle)
                logger.debug(f"Payoff matrix built successfully: {payoff_matrix}")
                
                # Solve the game theory problem
                logger.debug("Solving game theory...")
                move_probabilities = self._solve_game_theory(battle, payoff_matrix)
                logger.debug(f"Game theory solved successfully. Move probabilities: {move_probabilities}")
                
                # Send data to dashboard
                logger.debug("Sending data to dashboard...")
                try:
                    self.dashboard_connector.send_battle_state(
                        battle, 
                        payoff_matrix, 
                        move_probabilities
                    )
                    logger.debug("Dashboard update sent successfully")
                except Exception as e:
                    logger.error(f"Error sending data to dashboard: {str(e)}")
                
                # Select a move according to the probability distribution
                logger.debug("Selecting move from distribution...")
                selected_move = self._select_move_from_distribution(battle, move_probabilities)
                logger.debug(f"Selected move: {selected_move.id}")
                self.last_moves[battle.battle_tag] = selected_move
                move_order = self.create_order(selected_move)
                logger.debug(f"Created move order: {move_order}")
                return move_order
            except Exception as e:
                logger.error(f"Error in move selection: {str(e)}")
                logger.debug("Falling back to default move")
                return self.choose_default_move(battle)
        
        # If no moves are available, try switching
        logger.debug("No moves available, attempting to switch")
        if battle.available_switches:
            logger.debug(f"Available switches: {[pkmn.species for pkmn in battle.available_switches]}")
            switch_move = self.choose_random_switch(battle)
            logger.debug(f"Selected switch move: {switch_move}")
            return switch_move
        
        # If no moves or switches are available, use default move
        logger.debug("No switches available, using default move")
        default_move = self.choose_default_move(battle)
        logger.debug(f"Selected default move: {default_move}")
        return default_move
    
    def _solve_game_theory(self, battle, payoff_matrix):
        # Convert to format expected by C++ solver
        matrix_for_solver = []
        move_ids = []
        
        for our_move_id, opponent_moves in payoff_matrix.items():
            move_ids.append(our_move_id)
            row = []
            for opp_move_id, payoff in opponent_moves.items():
                row.append(payoff)
            matrix_for_solver.append(row)
        
        # Call the C++ solver
        mixed_strategy = nash_solver.solve_zero_sum_game(matrix_for_solver)
        
        # Return the probabilities for each move
        move_probabilities = {move_id: prob for move_id, prob in zip(move_ids, mixed_strategy)}
        
        return move_probabilities
    
    def _select_move_from_distribution(self, battle, move_probabilities):
        # Filter to only include available moves
        available_move_ids = {move.id: move for move in battle.available_moves}
        
        # Filter probabilities to only include available moves
        filtered_probs = {move_id: prob for move_id, prob in move_probabilities.items() 
                         if move_id in available_move_ids}
        
        # Normalize probabilities
        total_prob = sum(filtered_probs.values())
        if total_prob > 0:
            normalized_probs = {move_id: prob/total_prob for move_id, prob in filtered_probs.items()}
        else:
            # Fallback to uniform distribution
            normalized_probs = {move_id: 1.0/len(available_move_ids) for move_id in available_move_ids}
        
        # Select move based on probabilities
        r = random.random()
        cumulative_prob = 0.0
        
        for move_id, prob in normalized_probs.items():
            cumulative_prob += prob
            if r <= cumulative_prob:
                return available_move_ids[move_id]
        
        # Fallback to random move
        return random.choice(list(battle.available_moves))
    
    def choose_random_switch(self, battle):
        """Choose a random switch option from available switches.
        
        If no switches are available, falls back to choose_default_move.
        
        :param battle: Current battle
        :return: BattleOrder for the chosen switch
        """
        if len(battle.available_switches) > 0:
            # Choose a random Pokémon to switch to
            switch_pokemon = random.choice(battle.available_switches)
            return self.create_order(switch_pokemon)
        else:
            # No switches available, use default move
            return self.choose_default_move(battle)
    
    def choose_default_move(self, battle):
        """Choose a default move when no other options are available.
        
        :param battle: Current battle
        :return: BattleOrder for a random move or struggle
        """
        logger.debug("Choosing default move")
        
        # If we have any moves available, use a random one
        if battle.available_moves:
            selected_move = battle.available_moves[0]  # Use first available move as default
            logger.debug(f"Using first available move as default: {selected_move.id}")
            return self.create_order(selected_move)
            
        # If we have no moves but can switch, do that
        if battle.available_switches:
            logger.debug("No moves available but can switch, choosing random switch")
            return self.choose_random_switch(battle)
            
        # If we truly have no options, struggle
        logger.debug("No moves or switches available, using struggle")
        return self.create_order(None)  # This will result in a struggle
    
    def _battle_finished_callback(self, battle):
        """Called when a battle finishes."""
        # Record the final battle state
        won = battle.won
        self.data_collector.finalize_battle(battle, won=won)
        
        # Clear the last move for this battle
        if battle.battle_tag in self.last_moves:
            del self.last_moves[battle.battle_tag]
            
        # Let parent class handle the rest
        super()._battle_finished_callback(battle)