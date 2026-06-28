using System.Windows;

namespace MISS.Services;

public static class NotificationService
{
    public static void Info(string message) =>
        MessageBox.Show(message, "MISS", MessageBoxButton.OK, MessageBoxImage.Information);

    public static bool Confirm(string message) =>
        MessageBox.Show(message, "确认", MessageBoxButton.YesNo, MessageBoxImage.Warning) == MessageBoxResult.Yes;

    public static void Error(string message) =>
        MessageBox.Show(message, "错误", MessageBoxButton.OK, MessageBoxImage.Error);
}
