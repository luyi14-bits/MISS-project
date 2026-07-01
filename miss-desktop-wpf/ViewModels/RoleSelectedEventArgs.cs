// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System;
using MISS.Models;

namespace MISS.Views;

public class RoleSelectedEventArgs : EventArgs
{
    public RoleData Role { get; }
    public RoleSelectedEventArgs(RoleData role) => Role = role;
}
