import logging
import pytest
from services.desktop_bridge import ping_test


class TestPingTestLogging:
    def test_ping_test_logs_activity(self, caplog):
        caplog.set_level(logging.INFO, logger="desktop_bridge")

        result = ping_test()

        assert isinstance(result, dict)
        assert "ok" in result

        log_lines = [r.message for r in caplog.records
                     if r.name == "desktop_bridge" and r.levelno >= logging.INFO]

        assert len(log_lines) > 0, (
            "ping_test 应写入至少一条 INFO 日志（连接测试结果），"
            "当前零日志输出——用户排查 API 配置问题时无 audit trail"
        )
