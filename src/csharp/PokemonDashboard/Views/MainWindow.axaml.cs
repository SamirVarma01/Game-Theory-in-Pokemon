using Avalonia.Controls;
using Avalonia.Markup.Xaml;
using PokemonDashboard.ViewModels;

namespace PokemonDashboard.Views;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
    }

    private void InitializeComponent()
    {
        AvaloniaXamlLoader.Load(this);
    }
}