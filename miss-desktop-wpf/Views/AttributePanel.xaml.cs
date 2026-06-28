using System.Windows;
using System.Windows.Controls;
using MISS.ViewModels;

namespace MISS.Views;

public partial class AttributePanel : UserControl
{
    public AttributePanel()
    {
        InitializeComponent();
    }

    public void ShowIntimacyChange(int value, int change)
    {
        IntimacyChangeText.Text = change > 0 ? $"+{change}" : $"{change}";
    }

    private void EducationLevel_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
    {
        MainViewModel.Instance.IsCirnoMode = (int)e.NewValue == -100;
    }
}
