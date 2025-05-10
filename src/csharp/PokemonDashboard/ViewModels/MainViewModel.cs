using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Threading;
using Newtonsoft.Json;
using PokemonDashboard.Models;

namespace PokemonDashboard.ViewModels
{
    public class MainViewModel : ViewModelBase
    {
        private BattleState _currentBattle;
        private Thread _listenerThread;
        private TcpListener _server;
        private bool _isRunning;
        
        private string _battleInfo;
        public string BattleInfo
        {
            get => _battleInfo;
            set => SetProperty(ref _battleInfo, value);
        }
        
        private string _ourPokemonInfo;
        public string OurPokemonInfo
        {
            get => _ourPokemonInfo;
            set => SetProperty(ref _ourPokemonInfo, value);
        }
        
        private string _opponentPokemonInfo;
        public string OpponentPokemonInfo
        {
            get => _opponentPokemonInfo;
            set => SetProperty(ref _opponentPokemonInfo, value);
        }
        
        private string _payoffMatrixText;
        public string PayoffMatrixText
        {
            get => _payoffMatrixText;
            set => SetProperty(ref _payoffMatrixText, value);
        }
        
        private Dictionary<string, double> _moveProbabilities;
        private ObservableCollection<KeyValuePair<string, double>> _moveProbabilitiesCollection;
        
        public ObservableCollection<KeyValuePair<string, double>> MoveProbabilities
        {
            get => _moveProbabilitiesCollection;
            private set => SetProperty(ref _moveProbabilitiesCollection, value);
        }
        
        public MainViewModel()
        {
            BattleInfo = "Waiting for battle data...";
            OurPokemonInfo = "No Pokémon data available";
            OpponentPokemonInfo = "No Pokémon data available";
            PayoffMatrixText = "No payoff matrix available";
            _moveProbabilities = new Dictionary<string, double>();
            MoveProbabilities = new ObservableCollection<KeyValuePair<string, double>>();
            
            StartServer();
        }
        
        private void StartServer()
        {
            _isRunning = true;
            _listenerThread = new Thread(ListenForData);
            _listenerThread.IsBackground = true;
            _listenerThread.Start();
        }
        
        private void ListenForData()
        {
            try
            {
                _server = new TcpListener(IPAddress.Parse("127.0.0.1"), 8888);
                _server.Start();
                
                Console.WriteLine("Dashboard server started, listening on port 8888");
                
                while (_isRunning)
                {
                    try
                    {
                        using (TcpClient client = _server.AcceptTcpClient())
                        using (NetworkStream stream = client.GetStream())
                        {
                            // Read data
                            byte[] buffer = new byte[16384]; // Larger buffer
                            int bytesRead = stream.Read(buffer, 0, buffer.Length);
                            string data = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                            
                            // Parse battle state
                            try 
                            {
                                _currentBattle = JsonConvert.DeserializeObject<BattleState>(data);
                                
                                // Update UI on UI thread
                                Dispatcher.UIThread.Post(UpdateUI);
                            }
                            catch (Exception ex)
                            {
                                Console.WriteLine("Error parsing data: " + ex.Message);
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine("Client connection error: " + ex.Message);
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("Server error: " + ex.Message);
            }
        }
        
        private void UpdateUI()
        {
            if (_currentBattle == null)
                return;
                
            // Update battle info
            BattleInfo = $"Turn: {_currentBattle.Turn}, Weather: {_currentBattle.Weather}";
            
            // Update our Pokémon info
            if (_currentBattle.ActivePokemon?.Self != null)
            {
                var pokemon = _currentBattle.ActivePokemon.Self;
                var types = pokemon.Types != null ? string.Join(", ", pokemon.Types) : "Unknown";
                var hp = pokemon.Hp * 100;
                
                var movesText = "";
                if (pokemon.Moves != null)
                {
                    foreach (var move in pokemon.Moves)
                    {
                        movesText += $"\n  {move.Name} ({move.Type}) - Power: {move.BasePower}";
                    }
                }
                
                OurPokemonInfo = $"Our Pokémon: {pokemon.Species}\nTypes: {types}\nHP: {hp:F0}%{movesText}";
            }
            
            // Update opponent Pokémon info
            if (_currentBattle.ActivePokemon?.Opponent != null)
            {
                var pokemon = _currentBattle.ActivePokemon.Opponent;
                var types = pokemon.Types != null ? string.Join(", ", pokemon.Types) : "Unknown";
                var hp = pokemon.Hp * 100;
                
                var movesText = "";
                if (pokemon.Moves != null)
                {
                    foreach (var move in pokemon.Moves)
                    {
                        movesText += $"\n  {move.Name} ({move.Type}) - Power: {move.BasePower}";
                    }
                }
                
                OpponentPokemonInfo = $"Opponent's Pokémon: {pokemon.Species}\nTypes: {types}\nHP: {hp:F0}%{movesText}";
            }
            
            // Update payoff matrix
            if (_currentBattle.PayoffMatrix != null)
            {
                var matrixText = "Payoff Matrix:\n";
                
                // Get all opponent move IDs
                var oppMoveIds = new HashSet<string>();
                foreach (var ourMove in _currentBattle.PayoffMatrix)
                {
                    foreach (var oppMove in ourMove.Value)
                    {
                        oppMoveIds.Add(oppMove.Key);
                    }
                }
                
                // Build header row
                matrixText += "Our Move \\ Opp Move";
                foreach (var oppMoveId in oppMoveIds)
                {
                    matrixText += $"\t{oppMoveId}";
                }
                matrixText += "\n";
                
                // Build data rows
                foreach (var ourMove in _currentBattle.PayoffMatrix)
                {
                    matrixText += ourMove.Key;
                    
                    foreach (var oppMoveId in oppMoveIds)
                    {
                        if (ourMove.Value.TryGetValue(oppMoveId, out double payoff))
                        {
                            matrixText += $"\t{payoff:F2}";
                        }
                        else
                        {
                            matrixText += "\t-";
                        }
                    }
                    
                    matrixText += "\n";
                }
                
                PayoffMatrixText = matrixText;
            }
            
            // Update move probabilities
            if (_currentBattle.MoveProbabilities != null)
            {
                _moveProbabilities = _currentBattle.MoveProbabilities;
                MoveProbabilities.Clear();
                foreach (var kvp in _moveProbabilities)
                {
                    MoveProbabilities.Add(kvp);
                }
            }
        }
        
        protected bool SetProperty<T>(ref T field, T value, [System.Runtime.CompilerServices.CallerMemberName] string propertyName = null)
        {
            if (EqualityComparer<T>.Default.Equals(field, value)) return false;
            field = value;
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
            return true;
        }
        
        public new event PropertyChangedEventHandler PropertyChanged;
    }
}