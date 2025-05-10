from poke_env.data import GenData
from opponent_model import OpponentModel
import json
import os

class PayoffMatrixBuilder:
    def __init__(self, opponent_model=None):
        # Load type effectiveness data
        data_path = os.path.join(os.path.dirname(__file__), '../../data/type_chart.json')
        with open(data_path, 'r') as f:
            self.type_chart = json.load(f)
        
        # Initialize opponent model
        self.opponent_model = opponent_model or OpponentModel()
    
    def build_matrix(self, battle):
        our_moves = battle.available_moves
        opponent_move_probs = self.opponent_model.predict_moves(battle)
    
        if not opponent_move_probs:
            opponent_moves = []
            if hasattr(battle.opponent_active_pokemon, 'moves'):
                opponent_moves = list(battle.opponent_active_pokemon.moves.values())
            
            # If no opponent moves are known, make some assumptions
            if not opponent_moves and battle.opponent_active_pokemon:
                # Use possible moves based on opponent's type
                opponent_types = battle.opponent_active_pokemon.types
                opponent_moves = self._generate_possible_moves(opponent_types)
            
            # If we still have no moves, use a default move
            if not opponent_moves:
                from poke_env.environment.move import Move
                opponent_moves = [Move("tackle", gen=9)]  # Default to tackle if no moves are available
            
            # Create uniform distribution
            prob = 1.0 / len(opponent_moves)
            opponent_move_probs = {move.id: prob for move in opponent_moves}
        
        payoff_matrix = {}
        
        for our_move in our_moves:
            payoff_matrix[our_move.id] = {}
            
            # For each predicted opponent move
            for opp_move_id, prob in opponent_move_probs.items():
                # Find the move object
                opp_move = None
                if hasattr(battle.opponent_active_pokemon, 'moves'):
                    opp_move = battle.opponent_active_pokemon.moves.get(opp_move_id)
                
                # If we don't have the move object, create a dummy one based on ID
                if opp_move is None:
                    from poke_env.environment.move import Move
                    opp_move = Move(opp_move_id, gen=9)

                payoff = self._calculate_move_vs_move_payoff(
                    our_move, 
                    opp_move, 
                    battle.active_pokemon, 
                    battle.opponent_active_pokemon,
                    battle
                )
                
                # Weight the payoff by the probability
                payoff_matrix[our_move.id][opp_move_id] = payoff * prob
        
        return payoff_matrix
    
    def _calculate_move_vs_move_payoff(self, our_move, opp_move, our_pokemon, opp_pokemon, battle):
        we_go_first = self._determines_move_order(our_move, opp_move, our_pokemon, opp_pokemon)
        our_damage = self._calculate_move_damage(our_move, our_pokemon, opp_pokemon)
        opp_damage = self._calculate_move_damage(opp_move, opp_pokemon, our_pokemon)
        payoff = (our_damage / max(1, opp_pokemon.max_hp)) - (opp_damage / max(1, our_pokemon.max_hp))

        if self._is_super_effective(our_move, opp_pokemon):
            payoff += 0.2
        
        if hasattr(our_move, 'status') and our_move.status:
            payoff += 0.1
        
        return payoff
    
    def _determines_move_order(self, our_move, opp_move, our_pokemon, opp_pokemon):
    # Priority moves go first
        if our_move.priority > opp_move.priority:
            return True
        elif our_move.priority < opp_move.priority:
            return False
        
        # Equal priority, check Speed stat
        our_speed = our_pokemon.stats.get('spe', 0)
        opp_speed = opp_pokemon.stats.get('spe', 0)
        
        # Handle None values safely
        if our_speed is None:
            our_speed = 0
        if opp_speed is None:
            opp_speed = 0
            
        return our_speed >= opp_speed
    
    def _calculate_move_damage(self, move, attacker, defender):
        if move.category == 2:  # Status move
            return 0
        
        # Basic damage formula (simplified)
        level = attacker.level
        power = move.base_power
        
        # Use the appropriate attack and defense stats
        if move.category == 0:  # Physical
            attack = attacker.stats.get('atk', 50)
            defense = defender.stats.get('def', 50)
        else:  # Special
            attack = attacker.stats.get('spa', 50)
            defense = defender.stats.get('spd', 50)
        
        # Handle None values safely
        if attack is None:
            attack = 50  # Default value
        if defense is None:
            defense = 50  # Default value
        
        # Calculate base damage (simplified formula)
        base_damage = ((2 * level / 5 + 2) * power * attack / defense) / 50 + 2
        
        # Type effectiveness
        type_multiplier = self._calculate_type_effectiveness(move, defender)
        
        # STAB (Same Type Attack Bonus)
        stab = 1.5 if move.type in attacker.types else 1.0
        
        # Final damage
        damage = base_damage * type_multiplier * stab
        
        return damage
    
    def _calculate_type_effectiveness(self, move, defender):
        if move.category == 2:  # Status move
            return 1
        
        move_type = move.type
        multiplier = 1
        
        for defender_type in defender.types:
            if move_type in self.type_chart and defender_type in self.type_chart[move_type]:
                multiplier *= self.type_chart[move_type][defender_type]
        
        return multiplier
    
    def _is_super_effective(self, move, defender):
        effectiveness = self._calculate_type_effectiveness(move, defender)
        return effectiveness > 1
    
    def _generate_possible_moves(self, types):
        # Generate plausible moves based on Pokemon types
        # This is a placeholder - in a real implementation, you'd have a more sophisticated approach
        
        gen_data = GenData.from_gen(9)  # Gen 9 data
        possible_moves = []

        for type_name in types:
            # Find common moves of this type
            for move_id, move_data in gen_data.moves.items():
                if move_data.get('type') == type_name:
                    from poke_env.environment.move import Move
                    move = Move(move_id)
                    possible_moves.append(move)
                    if len(possible_moves) >= 4:  # Limit to 4 moves
                        break
        
        return possible_moves