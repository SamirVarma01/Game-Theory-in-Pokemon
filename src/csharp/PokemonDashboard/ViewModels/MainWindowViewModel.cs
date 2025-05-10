using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using CommunityToolkit.Mvvm.ComponentModel;
using System.Net;
using System.Text;
using System.Threading.Tasks;
using System.Threading;
using System.Text.Json;
using System.IO;
using System.Text.Json.Serialization;

namespace PokemonDashboard.ViewModels;

public partial class MainWindowViewModel : ObservableObject
{
    [ObservableProperty]
    private string _battleLog;

    [ObservableProperty]
    private int _wins;

    [ObservableProperty]
    private int _losses;

    [ObservableProperty]
    private double _winRate;

    private HttpListener _listener;
    private CancellationTokenSource _cts;

    public MainWindowViewModel()
    {
        BattleLog = "Welcome to Pokemon Battle Dashboard!\nWaiting for battles to begin...";
        Wins = 0;
        Losses = 0;
        WinRate = 0;
        
        // Start the HTTP server
        StartHttpServer();
    }

    private void StartHttpServer()
    {
        try
        {
            _listener = new HttpListener();
            _listener.Prefixes.Add("http://localhost:5000/");
            _cts = new CancellationTokenSource();

            Task.Run(async () =>
            {
                try
                {
                    _listener.Start();
                    AddBattleLogEntry("HTTP server started on port 5000");

                    while (!_cts.Token.IsCancellationRequested)
                    {
                        try
                        {
                            var context = await _listener.GetContextAsync();
                            var request = context.Request;
                            var response = context.Response;

                            if (request.HttpMethod == "POST")
                            {
                                using (var reader = new StreamReader(request.InputStream))
                                {
                                    var content = await reader.ReadToEndAsync();
                                    AddBattleLogEntry($"Received update: {content}");

                                    try
                                    {
                                        var update = JsonSerializer.Deserialize<BattleUpdate>(content);
                                        
                                        // Update UI on the main thread
                                        await Avalonia.Threading.Dispatcher.UIThread.InvokeAsync(() =>
                                        {
                                            if (!string.IsNullOrEmpty(update.Message))
                                            {
                                                AddBattleLogEntry(update.Message);
                                            }
                                            
                                            if (update.IsWin.HasValue)
                                            {
                                                if (update.IsWin.Value)
                                                {
                                                    Wins++;
                                                    AddBattleLogEntry("Win recorded!");
                                                }
                                                else
                                                {
                                                    Losses++;
                                                    AddBattleLogEntry("Loss recorded!");
                                                }
                                            }
                                        });
                                    }
                                    catch (JsonException ex)
                                    {
                                        AddBattleLogEntry($"Error parsing update: {ex.Message}");
                                    }
                                }

                                response.StatusCode = 200;
                            }
                            else
                            {
                                response.StatusCode = 405; // Method Not Allowed
                                AddBattleLogEntry($"Invalid request method: {request.HttpMethod}");
                            }

                            response.Close();
                        }
                        catch (Exception ex)
                        {
                            await Avalonia.Threading.Dispatcher.UIThread.InvokeAsync(() =>
                            {
                                AddBattleLogEntry($"Error processing request: {ex.Message}");
                            });
                        }
                    }
                }
                catch (Exception ex)
                {
                    await Avalonia.Threading.Dispatcher.UIThread.InvokeAsync(() =>
                    {
                        AddBattleLogEntry($"Server error: {ex.Message}");
                    });
                }
            }, _cts.Token);
        }
        catch (Exception ex)
        {
            AddBattleLogEntry($"Failed to start server: {ex.Message}");
        }
    }

    partial void OnWinsChanged(int value)
    {
        UpdateWinRate();
    }

    partial void OnLossesChanged(int value)
    {
        UpdateWinRate();
    }

    private void UpdateWinRate()
    {
        int totalGames = Wins + Losses;
        WinRate = totalGames > 0 ? (double)Wins / totalGames * 100 : 0;
        AddBattleLogEntry($"Win rate updated: {WinRate:F1}%");
    }

    public void AddBattleLogEntry(string entry)
    {
        BattleLog += $"\n{DateTime.Now:HH:mm:ss} - {entry}";
    }

    public void StopServer()
    {
        _cts?.Cancel();
        _listener?.Stop();
        _listener?.Close();
    }
}

public class BattleUpdate
{
    public string Message { get; set; }
    [JsonPropertyName("isWin")]
    public bool? IsWin { get; set; }
}
