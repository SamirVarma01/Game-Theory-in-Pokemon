using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace PokemonDashboard.Models
{
    public class BattleState
    {
        public ActivePokemonPair? ActivePokemon { get; set; }
        public Dictionary<string, Dictionary<string, double>>? PayoffMatrix { get; set; }
        public Dictionary<string, double>? MoveProbabilities { get; set; }
        public int Turn { get; set; }
        public string? Weather { get; set; }
        public List<string>? Fields { get; set; }
    }
    
    public class ActivePokemonPair
    {
        public Pokemon? Self { get; set; }
        public Pokemon? Opponent { get; set; }
    }
    
    public class Pokemon
    {
        public string? Species { get; set; }
        public double Hp { get; set; }
        public List<string>? Types { get; set; }
        public List<Move>? Moves { get; set; }
    }
    
    public class Move
    {
        public string? Id { get; set; }
        public string? Name { get; set; }
        public string? Type { get; set; }
        public int BasePower { get; set; }
        public int Category { get; set; }
    }
}