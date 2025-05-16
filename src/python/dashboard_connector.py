import requests
import json

class DashboardConnector:
    def __init__(self, host="localhost", port=5000):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
    
    def send_battle_state(self, battle, payoff_matrix, move_probabilities):
        battle_state = {
            "active_pokemon": {
                "self": self._extract_pokemon_data(battle.active_pokemon),
                "opponent": self._extract_pokemon_data(battle.opponent_active_pokemon)
            },
            "payoff_matrix": payoff_matrix,
            "move_probabilities": move_probabilities,
            "turn": battle.turn,
            "weather": str(battle.weather),
            "fields": [str(field) for field in battle.fields]
        }

        self._send_to_dashboard(battle_state)
    
    def _extract_pokemon_data(self, pokemon):
        if not pokemon:
            return None
        
        return {
            "species": pokemon.species,
            "hp": pokemon.current_hp_fraction,
            "types": [str(type_) for type_ in pokemon.types],
            "moves": [
                {
                    "id": move.id,
                    "name": move.id.replace("-", " ").title(),
                    "type": str(move.type),
                    "base_power": move.base_power,
                    "category": move.category
                } 
                for move in pokemon.moves.values()
            ] if hasattr(pokemon, 'moves') else []
        }
    
    def _send_to_dashboard(self, data):
        try:
            response = requests.post(
                f"{self.base_url}/battle-state",
                json=data,
                timeout=1
            )
            if response.status_code != 200:
                print(f"Error sending data to dashboard: {response.status_code}")
        except requests.exceptions.RequestException as e:
            if not hasattr(self, '_logged_connection_error'):
                print("Dashboard not running - continuing without visualization")
                self._logged_connection_error = True
        except Exception as e:
            print(f"Error sending data to dashboard: {e}")