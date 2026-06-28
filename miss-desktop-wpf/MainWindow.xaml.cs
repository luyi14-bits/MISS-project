using System.Windows;
using MISS.Views;
using MISS.ViewModels;

namespace MISS;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        DataContext = MainViewModel.Instance;
    }

    public void OpenSettings()
    {
        new SettingsWindow { Owner = this }.ShowDialog();
    }
}
