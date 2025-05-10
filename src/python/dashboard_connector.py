import socket
import json

class DashboardConnector:
    def __init__(self, host="localhost", port=8888):
        self.host = host
        self.port = port
    
    def send_battle_state(self, battle, payoff_matrix, move_probabilities):
        # Prepare data for the dashboard
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
            # Connect to the C# dashboard
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)  # Set a timeout to avoid hanging
            sock.connect((self.host, self.port))
            
            # Send JSON data
            json_data = json.dumps(data)
            sock.sendall(json_data.encode())
            
            sock.close()
        except ConnectionRefusedError:
            # Dashboard isn't running, just log once
            if not hasattr(self, '_logged_connection_error'):
                print("Dashboard not running - continuing without visualization")
                self._logged_connection_error = True
        except Exception as e:
            print(f"Error sending data to dashboard: {e}")
            # Continue without dashboard if connection fails