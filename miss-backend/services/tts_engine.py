# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
import asyncio, logging

try:
    import edge_tts
    _HAS_EDGE = True
except ImportError:
    _HAS_EDGE = False


VOICE_MAP = {
    "zh-CN-XiaoxiaoNeural": "晓晓（女·温柔，默认）",
    "zh-CN-YunxiNeural": "云希（男·青年）",
    "zh-CN-XiaoyiNeural": "晓依（女·活泼）",
    "zh-CN-YunyangNeural": "云扬（男·新闻）",
    "ja-JP-NanamiNeural": "七海（日语·女）",
}

_DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"


async def synthesize(text: str, voice: str = _DEFAULT_VOICE) -> bytes:
    if not _HAS_EDGE:
        logging.getLogger("tts_engine").warning("edge-tts not installed")
        return b""
    try:
        communicate = edge_tts.Communicate(text, voice)
        chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        return b"".join(chunks)
    except Exception as e:
        logging.getLogger("tts_engine").warning("synthesize failed: %s", e)
        return b""
