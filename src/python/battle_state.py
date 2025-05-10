class BattleStateTracker:
    def __init__(self):
        self.battle_history = {}
    
    def update(self, battle):
        battle_id = battle.battle_tag
        if battle_id not in self.battle_history:
            self.battle_history[battle_id] = []
    
        current_state = {
                "turn": battle.turn,
                "active_pokemon": {
                    "self": self._extract_pokemon_data(battle.active_pokemon),
                    "opponent": self._extract_pokemon_data(battle.opponent_active_pokemon)
                },
                "team": {
                    "self": {p.species: self._extract_pokemon_data(p) for p in battle.team.values()},
                    "opponent": {p.species: self._extract_pokemon_data(p) for p in battle.opponent_team.values() if p.species}
                },
                "weather": battle.weather,
                "fields": battle.fields
            }
        
        self.battle_history[battle_id].append(current_state)
        return current_state
    
    def _extract_pokemon_data(self, pokemon):
        if not pokemon:
            return None
        
        return {
            "species": pokemon.species,
            "hp": pokemon.current_hp_fraction,
            "max_hp": pokemon.max_hp,
            "level": pokemon.level,
            "status": pokemon.status,
            "types": pokemon.types,
            "moves": [move.id for move in pokemon.moves.values()] if hasattr(pokemon, 'moves') else [],
            "stats": pokemon.stats if hasattr(pokemon, 'stats') else {}
        }