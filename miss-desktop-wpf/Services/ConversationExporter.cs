// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.IO;
using System.Text;
using System.Text.Json;
using MISS.Controls;
using MISS.Models;

namespace MISS.Services;

public static class ConversationExporter
{
    private static readonly JsonSerializerOptions JsonOpts = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
    };

    /// <summary>
    /// Export conversation as a formatted JSON file.
    /// </summary>
    public static void ExportToJson(List<ChatMessage> messages, SessionData session, string outputPath)
    {
        var data = new
        {
            session_id = session.Id,
            session_title = session.Title,
            role_name = session.RoleName,
            created_at = session.CreatedAt,
            exported_at = DateTime.Now,
            total_messages = messages.Count,
            messages = messages.Select(m => new
            {
                sender = m.Sender,
                role = m.RoleName,
                text = m.Text,
                inner_thought = m.InnerThought,
                is_user = m.IsUser,
                timestamp = m.Timestamp
            })
        };

        string json = JsonSerializer.Serialize(data, JsonOpts);
        File.WriteAllText(outputPath, json, Encoding.UTF8);
    }

    /// <summary>
    /// Export conversation as a self-contained HTML file with styled message bubbles.
    /// </summary>
    public static void ExportToHtml(List<ChatMessage> messages, SessionData session, RoleData? role, string outputPath)
    {
        var sb = new StringBuilder();
        sb.AppendLine("<!DOCTYPE html>");
        sb.AppendLine("<html lang=\"zh-CN\">");
        sb.AppendLine("<head><meta charset=\"UTF-8\">");
        sb.AppendLine("<title>对话导出 — " + EscapeHtml(session.Title) + "</title>");
        sb.AppendLine("<style>");
        sb.AppendLine("body{font-family:-apple-system,'Microsoft YaHei',sans-serif;max-width:720px;margin:40px auto;padding:0 20px;background:#FDF8F0;color:#4A3728}");
        sb.AppendLine("h1{font-size:18px;border-bottom:1px solid #E8DDD4;padding-bottom:10px}");
        sb.AppendLine(".meta{font-size:12px;color:#8B7355;margin-bottom:24px}");
        sb.AppendLine(".msg{display:flex;margin-bottom:14px;gap:10px}");
        sb.AppendLine(".msg.user{flex-direction:row-reverse}");
        sb.AppendLine(".avatar{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:bold;flex-shrink:0}");
        sb.AppendLine(".avatar.miss{background:#FBE5E0;color:#C05A4E}");
        sb.AppendLine(".avatar.user{background:#F0E6DA;color:#8B7355}");
        sb.AppendLine(".bubble{padding:10px 14px;border-radius:14px;font-size:14px;line-height:1.55;max-width:78%;word-break:break-word}");
        sb.AppendLine(".user .bubble{background:#F0E6DA;border-bottom-right-radius:4px}");
        sb.AppendLine(".miss .bubble{background:#FBE5E0;border-bottom-left-radius:4px}");
        sb.AppendLine(".inner{font-size:11px;color:#8B7355;font-style:italic;margin-top:4px;padding:4px 8px;background:#FFF8F0;border-radius:6px;border-left:2px solid #D4A857}");
        sb.AppendLine(".sender{font-size:11px;color:#8B7355;margin-bottom:2px}");
        sb.AppendLine("</style></head><body>");
        sb.AppendLine("<h1>💬 " + EscapeHtml(session.Title) + "</h1>");
        sb.AppendLine("<div class=\"meta\">角色: " + EscapeHtml(session.RoleName ?? "无") + " · 消息数: " + messages.Count + " · 导出时间: " + DateTime.Now.ToString("yyyy-MM-dd HH:mm") + "</div>");

        foreach (var m in messages)
        {
            string cls = m.IsUser ? "user" : "miss";
            string sender = m.IsUser ? "我" : (m.RoleName ?? "MISS");
            string avatarLetter = m.IsUser ? "✦" : (m.RoleName?.Length > 0 ? m.RoleName[..1] : "M");

            sb.AppendLine("<div class=\"msg " + cls + "\">");
            sb.AppendLine("<div class=\"avatar " + cls + "\">" + EscapeHtml(avatarLetter) + "</div>");
            sb.AppendLine("<div class=\"body\">");
            sb.AppendLine("<div class=\"sender\">" + EscapeHtml(sender) + "</div>");
            sb.AppendLine("<div class=\"bubble\">" + EscapeHtml(m.Text).Replace("\n", "<br>") + "</div>");
            if (!string.IsNullOrEmpty(m.InnerThought))
                sb.AppendLine("<div class=\"inner\">💭 " + EscapeHtml(m.InnerThought).Replace("\n", "<br>") + "</div>");
            sb.AppendLine("</div></div>");
        }

        sb.AppendLine("</body></html>");
        File.WriteAllText(outputPath, sb.ToString(), Encoding.UTF8);
    }

    /// <summary>
    /// Export conversation as a readable Markdown file.
    /// </summary>
    public static void ExportToMarkdown(List<ChatMessage> messages, SessionData session, RoleData? role, string outputPath)
    {
        var sb = new StringBuilder();
        sb.AppendLine("# 对话导出：" + session.Title);
        sb.AppendLine();
        sb.AppendLine("- **角色**: " + (session.RoleName ?? "无"));
        sb.AppendLine("- **消息数**: " + messages.Count);
        sb.AppendLine("- **导出时间**: " + DateTime.Now.ToString("yyyy-MM-dd HH:mm"));
        sb.AppendLine();
        sb.AppendLine("---");
        sb.AppendLine();

        foreach (var m in messages)
        {
            string sender = m.IsUser ? "**我**" : ("**" + (m.RoleName ?? "MISS") + "**");
            sb.AppendLine("### " + sender + "  " + m.Timestamp.ToString("MM-dd HH:mm"));
            sb.AppendLine();
            sb.AppendLine(m.Text);
            sb.AppendLine();
            if (!string.IsNullOrEmpty(m.InnerThought))
            {
                sb.AppendLine("> 💭 *" + m.InnerThought + "*");
                sb.AppendLine();
            }
            sb.AppendLine("---");
            sb.AppendLine();
        }

        File.WriteAllText(outputPath, sb.ToString(), Encoding.UTF8);
    }

    private static string EscapeHtml(string? text)
    {
        if (string.IsNullOrEmpty(text)) return "";
        return text.Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;")
                   .Replace("\"", "&quot;").Replace("'", "&#39;");
    }
}
