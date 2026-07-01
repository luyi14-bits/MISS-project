// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using MISS.Controls;
using MISS.Models;

namespace MISS.Services;

public interface ILocalStore
{
    List<SessionData> LoadSessions();
    void SaveSessions(List<SessionData> sessions);
    List<ChatMessage> LoadMessages(int sessionId);
    void SaveMessages(int sessionId, List<ChatMessage> messages);
    void DeleteMessages(int sessionId);
    void DeleteSession(int sessionId);
    List<RoleData> LoadRoles();
    void SaveRoles(List<RoleData> roles);
    void SaveRole(RoleData role);
    void DeleteRole(string name);
    List<RoleData> GetBuiltinRoles();
    SettingsData? LoadSettings();
    void SaveSettings(SettingsData settings);
}
