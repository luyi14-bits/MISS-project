using System;
using System.Globalization;
using System.Windows;
using System.Windows.Data;

namespace MISS.Views;

public class FirstCharConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        var name = value as string;
        if (string.IsNullOrEmpty(name))
            return "?";
        return name[0].ToString();
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        throw new NotSupportedException();
    }
}
