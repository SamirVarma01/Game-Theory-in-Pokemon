import json
import os
import time
from datetime import datetime

class BattleDataCollector:
    """Records battle data for training opponent models."""
    
    def __init__(self, data_dir="logs/battle_data"):
        """Initialize the data collector.
        
        Args:
            data_dir: Directory to store battle data
        """
        self.data_dir = data_dir
        self.current_battles = {}
        
        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
    
    def record_battle_state(self, battle, turn_num, our_move=None, opponent_move=None):
        """Record the current state of a battle.
        
        Args:
            battle: Battle object
            turn_num: Current turn number
            our_move: Move we selected (if known)
            opponent_move: Move opponent selected (if known)
        """
        battle_id = battle.battle_tag
        
        # Initialize battle record if this is a new battle
        if battle_id not in self.current_battles:
            self.current_battles[battle_id] = {
                "battle_id": battle_id,
                "format": battle.format,
                "started_at": datetime.now().isoformat(),
                "our_team": self._extract_team_data(battle.team),
                "opponent_team": {},  # Will be filled as opponent reveals Pokémon
                "turns": []
            }
        
        # Get current battle state
        battle_state = {
            "turn": turn_num,
            "weather": str(battle.weather),
            "fields": [str(field) for field in battle.fields],
            "our_active": self._extract_pokemon_data(battle.active_pokemon),
            "opponent_active": self._extract_pokemon_data(battle.opponent_active_pokemon),
            "our_move": self._extract_move_data(our_move) if our_move else None,
            "opponent_move": self._extract_move_data(opponent_move) if opponent_move else None
        }
        
        # Update opponent team data if new info is available
        if battle.opponent_active_pokemon:
            species = battle.opponent_active_pokemon.species
            if species and species not in self.current_battles[battle_id]["opponent_team"]:
                self.current_battles[battle_id]["opponent_team"][species] = \
                    self._extract_pokemon_data(battle.opponent_active_pokemon)
        
        # Add battle state to turns
        self.current_battles[battle_id]["turns"].append(battle_state)
    
    def finalize_battle(self, battle, won=None):
        """Finalize and save battle data when a battle ends.
        
        Args:
            battle: Battle object
            won: True if we won, False if we lost, None if tied
        """
        battle_id = battle.battle_tag
        
        if battle_id not in self.current_battles:
            return
        
        # Add battle result
        self.current_battles[battle_id]["result"] = "win" if won else "loss" 
        self.current_battles[battle_id]["ended_at"] = datetime.now().isoformat()
        
        # Save to file
        filename = f"{battle_id}_{int(time.time())}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(self.current_battles[battle_id], f, indent=2)
        
        # Remove from current battles
        del self.current_battles[battle_id]
    
    def _extract_team_data(self, team):
        """Extract relevant data from a team.
        
        Args:
            team: Dictionary of Pokemon objects
            
        Returns:
            Dictionary with pokemon data
        """
        team_data = {}
        
        for pokemon_id, pokemon in team.items():
            team_data[pokemon_id] = self._extract_pokemon_data(pokemon)
        
        return team_data
    
    def _extract_pokemon_data(self, pokemon):
        """Extract relevant data from a Pokemon.
        
        Args:
            pokemon: Pokemon object
            
        Returns:
            Dictionary with pokemon data
        """
        if not pokemon:
            return None
        
        data = {
            "species": pokemon.species,
            "types": [str(t) for t in pokemon.types],
            "level": pokemon.level,
            "hp": pokemon.current_hp_fraction if hasattr(pokemon, 'current_hp_fraction') else None,
            "status": str(pokemon.status) if pokemon.status else None,
        }
        
        if hasattr(pokemon, 'moves') and pokemon.moves:
            data["moves"] = {
                move_id: self._extract_move_data(move) 
                for move_id, move in pokemon.moves.items()
            }
        
        if hasattr(pokemon, 'stats') and pokemon.stats:
            data["stats"] = pokemon.stats
            
        return data
    
    def _extract_move_data(self, move):
        """Extract relevant data from a Move.
        
        Args:
            move: Move object
            
        Returns:
            Dictionary with move data
        """
        if not move:
            return None
            
        return {
            "id": move.id,
            "type": str(move.type),
            "base_power": move.base_power,
            "category": move.category,
            "accuracy": move.accuracy,
            "priority": move.priority
        }