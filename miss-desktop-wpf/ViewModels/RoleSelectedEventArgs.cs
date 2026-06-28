using System;
using MISS.Models;

namespace MISS.Views;

public class RoleSelectedEventArgs : EventArgs
{
    public RoleData Role { get; }
    public RoleSelectedEventArgs(RoleData role) => Role = role;
}
