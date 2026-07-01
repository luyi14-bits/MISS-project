# Phase 5+6 开源包调研报告 — PM 审批版

> 调研日期：2026-07-01 | 给主程用的执行版，砍掉了学术讨论

---

## 结论前置：可以直接用的，不需要换的，不能碰的

### ✅ 四个直接可用、不需要换的包

| 包 | 为什么安全 | 需要做什么 |
|---|---|---|
| **NAudio** (NuGet) | MIT许可，.NET基金会旗下，无已知CVE，1200万下载量 | 无。本来就是spec选定的 |
| **LiteDB** (NuGet) | MIT许可，嵌入式NoSQL，单DLL<450KB，支持AES加密 | 无。已经在用 |
| **Pillow** (pip) | HPND许可（≈MIT），日下载4000万，成熟稳定 | 注意PyInstaller打包需要hook C扩展。另外查一下当前版本——页面抓到的是10.1.0（2023年），应该已经有11.x了 |
| **httpx** (pip) | BSD许可，同步+异步双模式，API比aiohttp友好，无CVE | **建议替换aiohttp**。aiohttp在客户端模式下的两个CVE不影响我们，但httpx更干净，而且API更好用 |

---

### ⚠️ 可以用但有注意事项的

| 包 | 风险 | 应对 |
|---|---|---|
| **edge-tts** (pip) | **这是最大的单点风险。** 它不是微软官方API，是逆向工程WebSocket端点。微软随时可以改协议。另外LGPLv3许可——闭源商业分发需要注意义务 | **短期**：继续用。**中期**：准备pyttsx3作为离线降级方案（不需要网络，但音色较机械）。如果将来用户反馈音质不行，再考虑Piper TTS的MIT原始版本（rhasspy/piper归档但代码是MIT，可fork） |
| **pydantic v2** (pip) | PyInstaller打包时Rust核心pydantic-core需要hidden-import配置 | PyInstaller spec里加`--collect-all pydantic`，不是什么大事。主程应该知道 |
| **instructor** (pip) | 本身安全（MIT），但sourcetarball 70MB（含大量测试数据）。体积对桌面应用没啥影响 | 检查一下依赖树有没有把anthropic SDK拉进来——我们不用Claude就不要装上 |

---

### ❌ 不能碰的

| 包 | 死因 |
|---|---|
| **Coqui TTS** | 公司已死，仓库归档。死了。 |
| **gTTS** | 依赖Google Translate非官方API，随时被封。 |
| **Piper TTS (OHF-Voice/piper1-gpl)** | 新维护者改成了**GPL-3.0**。闭源桌面应用不能静态链接GPL代码。用原始MIT版本（rhasspy/piper）fork可以但它是archived。 |
| **Fish Speech / OpenVoice / RVC** | 这些是声音克隆模型。每个模型500MB-2GB+，需要GPU推理。不适合嵌入桌面exe。如果将来做云端SaaS版再考虑。 |

---

## 按Task给建议

### Task 2 (RoleFactory LLM一键生成)

直接用现有的`instructor`+Pydantic，不需要新包。`RoleFactory.generate()`用instructor做structured output，spec里定义的`GeneratedRole` Pydantic模型已经够用了。唯一需要注意的是——你现在instructor用的是TOOLS模式（`llm_caller.py`当前就是这样），如果换成纯OpenAI API（等主程按我上次的方案改了之后），`RoleFactory`单独保留instructor就行。两个场景不冲突。

### Task 3 (KnowledgeDomainEngine前置注入)

不需要任何新包。这个Task只是往prompt里塞一段XML，是模板引擎的事。`Jinja2`已经有了。

### Task 6 (TTS引擎)

**edge-tts → pip install edge-tts。** 这是spec选定的方案，调研确认它维护活跃、安装简单、音质高。唯一需要注意的是——它不是官方API。在README和代码注释里标注清楚"依赖微软Edge TTS非官方端点，未来可能需要迁移"。

如果将来要做离线版：
- **pyttsx3**：直接用，系统自带语音引擎，Windows SAPI5音色比较机械但完全离线。**MPL-2.0许可，商业可用**。
- **Piper TTS (原始MIT版)**：rhasspy/piper已archive但代码是MIT，可从GitHub下载历史release。中文模型可用，音质比pyttsx3好但不如edge-tts。

建议：**现在不换，继续用edge-tts。在TTS引擎里加一个抽象层（TTSEngine基类），将来要换pyttsx3或Piper的时候只换实现不换接口。**

### Task 7 (C# AudioPlayer)

**NAudio → NuGet安装。** 调研没有发现任何需要换的理由。最成熟的.NET音频库，MIT许可，1200万次下载。

### P6-R4 (DALL-E头像生成)

**OpenAI Python SDK已经有DALL-E支持，不需要新包。** 生成的图片用Pillow做格式转换/缩放到256x256。头像存入`%APPDATA%/MISS/avatars/`目录。

不过有个比spec更好的方案：**在生成的PNG头像里嵌入Character Card格式的元数据。** SillyTavern生态里所有角色图像都用这种格式——PNG chunk里嵌Base64 JSON（角色名、描述、属性、领域标签等）。这样做的好处：
1. 头像图片本身就是可移植的角色定义文件
2. 跟ST生态互操作——用户可以把MISS生成的角色卡导入SilkyTavern
3. 技术上只要用Pillow写PNG tEXt chunk，不增加依赖

如果认可这个方向，Task 2的`RoleFactory.generate()`最后一步多做一个PNG嵌入。

---

## 审计清单（给主程）

| 动作 | 优先级 |
|------|--------|
| pip install edge-tts | P0 — Task 6 blocker |
| NuGet NAudio | P0 — Task 7 blocker |
| 检查instructor依赖树有没有anthropic SDK | P1 — 如果有就排除，减体积 |
| PyInstaller spec加`--collect-all pydantic` | P1 — 打包前必须做 |
| aiohttp → httpx（可选）| P2 — 不是阻塞项，但改了更干净 |
| 设计TTSEngine抽象基类 | P2 — 不改也行，但将来换引擎成本低 |
| 研究Character Card PNG嵌入方案 | P2 — spec之外的建议，效果好可以做 |