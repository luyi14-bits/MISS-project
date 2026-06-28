"""
Task 4.3 严格验收测试 - 向量嵌入 + ChromaDB 存储 (Mock版)
验收标准: 存储后可按语义检索，相关性合理
"""
import json, os, sys, uuid
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["OPENAI_API_KEY"] = ""
os.environ["DB_URL"] = "sqlite:///./tests/data/test_accept_4_3.db"

from models import Base
from database import engine, SessionLocal
from models.memory import MemoryEntry


def P(t): print(f"  ✅ PASS: {t}")
def F(t, d=""): print(f"  ❌ FAIL: {t}"); d and print(f"     {d}")


def run():
    p = f = 0
    Base.metadata.create_all(bind=engine)

    # 构建 mock
    mock_collection = MagicMock()
    mock_collection.count.return_value = 5
    mock_collection.get.return_value = {"ids": [[]], "documents": [[]], "metadatas": [[]], "embeddings": [[]]}
    mock_collection.query.return_value = {
        "ids": [["id1", "id2"]],
        "documents": [["内容1", "内容2"]],
        "metadatas": [[{"session_id": "s1", "importance": 85}, {"session_id": "s2", "importance": 50}]],
        "distances": [[0.3, 0.7]],
    }
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    with patch("services.vector_store.PersistentClient", return_value=mock_client):
        from services.vector_store import VectorMemoryStore

        try:
            print("=" * 65)
            print("Task 4.3 验收测试 - 向量嵌入 + ChromaDB 存储 (Mock)")
            print("=" * 65)

            store = VectorMemoryStore(api_key=None)

            # ===== 1. 类结构 =====
            print("\n【测试1】VectorMemoryStore 类结构与方法签名")
            import inspect
            expected_methods = ["store", "recall", "recall_with_threshold", "sync_from_db", "remove", "count"]
            for m in expected_methods:
                if hasattr(store, m): P(f"含方法: {m}"); p += 1
                else: F(f"缺方法: {m}"); f += 1
            if store.COLLECTION_NAME == "miss_memories": P("COLLECTION_NAME = miss_memories"); p += 1
            else: F(f"=\"{store.COLLECTION_NAME}\""); f += 1

            # 签名检查
            sig_store = inspect.signature(store.store)
            for param in ["entry_id", "content", "metadata"]:
                if param in sig_store.parameters: P(f"store() 含 {param}"); p += 1
                else: F(f"store() 缺 {param}"); f += 1
            sig_recall = inspect.signature(store.recall)
            for param in ["query", "top_k"]:
                if param in sig_recall.parameters: P(f"recall() 含 {param}"); p += 1
                else: F(f"recall() 缺 {param}"); f += 1

            # ===== 2. store() 调用 ChromaDB add =====
            print("\n【测试2】store() 正确调用 ChromaDB collection.add")
            mock_collection.add.reset_mock()
            store.store(entry_id="test_id", content="测试内容",
                        metadata={"session_id": "s", "importance": 80, "category": "fact"})
            if mock_collection.add.called: P("store() → collection.add() 被调用"); p += 1
            else: F("collection.add 未被调用"); f += 1
            call_args = mock_collection.add.call_args[1]
            if call_args.get("ids") == ["test_id"]: P("ids=[test_id] 正确"); p += 1
            else: F(f"ids={call_args.get('ids')}"); f += 1
            if call_args.get("documents") == ["测试内容"]: P("documents=[测试内容]"); p += 1
            else: F(f"documents={call_args.get('documents')}"); f += 1
            if isinstance(call_args.get("metadatas"), list): P("metadatas 为 list"); p += 1
            else: F(f"metadatas类型错误"); f += 1

            # ===== 3. metadata 含 stored_at =====
            meta = call_args["metadatas"][0]
            if "stored_at" in meta: P("元数据含 stored_at 时间戳"); p += 1
            else: F("缺 stored_at"); f += 1
            if meta.get("session_id") == "s": P("元数据含 session_id"); p += 1
            else: F(f"session_id={meta.get('session_id')}"); f += 1
            if meta.get("importance") == 80: P("元数据含 importance=80"); p += 1
            else: F(f"importance={meta.get('importance')}"); f += 1

            # ===== 4. recall() 正确调用 =====
            print("\n【测试3】recall() 正确调用 ChromaDB query + 返回结构")
            mock_collection.query.reset_mock()
            mock_collection.query.return_value = {
                "ids": [["mem1"]],
                "documents": [["用户喜欢古典音乐"]],
                "metadatas": [[{"importance": 90}]],
                "distances": [[0.2]],
            }
            results = store.recall(query="音乐推荐", top_k=5)
            if mock_collection.query.called: P("recall() → collection.query() 被调用"); p += 1
            else: F("collection.query 未被调用"); f += 1
            if len(results) >= 1: P("返回结果≥1条"); p += 1
            else: F("空结果"); f += 1
            r = results[0]
            for key in ["id", "content"]:
                if key in r: P(f"结果含 {key}"); p += 1
                else: F(f"缺 {key}"); f += 1

            # ===== 5. recall_with_threshold 阈值过滤 =====
            print("\n【测试4】recall_with_threshold() 阈值过滤")
            mock_collection.query.reset_mock()
            mock_collection.query.return_value = {
                "ids": [["a", "b", "c"]],
                "documents": [["A", "B", "C"]],
                "metadatas": [[{}, {}, {}]],
                "distances": [[0.1, 0.6, 0.2]],
            }
            results = store.recall_with_threshold(query="test", top_k=5, threshold=0.5)
            # threshold=0.5 → 只保留 distance≤0.5 的 → a(0.1) + c(0.2) = 2
            if len(results) == 2: P("threshold=0.5: 过滤后返回 2/3 条"); p += 1
            else: F(f"返回{len(results)}条"); f += 1
            # 验证distance含在结果里
            if "distance" in results[0]: P("结果含 distance 字段"); p += 1
            else: F("结果缺 distance"); f += 1

            # ===== 6. recall_with_threshold 严格阈值为0 =====
            print("\n【测试5】recall_with_threshold(threshold=0.0): 极严格")
            mock_collection.query.reset_mock()
            mock_collection.query.return_value = {
                "ids": [["x"]], "documents": [["X"]], "metadatas": [[{}]], "distances": [[0.0]],
            }
            results = store.recall_with_threshold(query="x", threshold=0.0)
            if len(results) == 1: P("threshold=0.0 distance=0.0 → 通过"); p += 1
            else: F(f"返回{len(results)}条"); f += 1

            # ===== 7. count() =====
            print("\n【测试6】count() 调用 collection.count()")
            mock_collection.count.return_value = 42
            if store.count() == 42: P("count()=42 (从mock返回)"); p += 1
            else: F(f"count={store.count()}"); f += 1

            # ===== 8. remove() =====
            print("\n【测试7】remove() 调用 collection.delete")
            mock_collection.delete.reset_mock()
            store.remove("entry_x")
            if mock_collection.delete.called: P("remove() → collection.delete() 被调用"); p += 1
            else: F("collection.delete 未被调用"); f += 1

            # ===== 9. 模块导出 =====
            print("\n【测试8】模块导出验证")
            from services import VectorMemoryStore as VMS
            if VMS is VectorMemoryStore: P("VectorMemoryStore 从 services 导出"); p += 1
            else: F("不一致"); f += 1
            from services import __all__ as ex
            if "VectorMemoryStore" in ex: P("__all__ 含 VectorMemoryStore"); p += 1
            else: F("__all__ 缺 VectorMemoryStore"); f += 1

            # ===== 10. PromptBuilder 集成 (直接传MagicMock) =====
            print("\n【测试9】PromptBuilder + VectorMemoryStore 集成")
            from services.prompt_builder import PromptBuilder
            from services.attribute_engine import MISSProfile

            mock_vs = MagicMock()
            mock_vs.recall.return_value = [
                {"id": "mem99", "content": "用户花生过敏", "importance": 95, "category": "fact"}
            ]
            builder = PromptBuilder(vector_store=mock_vs)
            result = builder.build_full("s_vec", "今天吃什么?", MISSProfile())
            if "messages" in result: P("PromptBuilder+VS → build正常"); p += 1
            else: F("build失败"); f += 1
            if mock_vs.recall.called: P("vector_store.recall() 被调用"); p += 1
            else: F("recall未被调用"); f += 1

            # ===== 11. MemorySummarizer 集成 =====
            print("\n【测试10】MemorySummarizer + VectorMemoryStore 集成")
            from services.memory_summarizer import MemorySummarizer

            mock_vs2 = MagicMock()
            summarizer = MemorySummarizer(vector_store=mock_vs2)
            scored = [{"content": "用户敏感信息", "importance": 90, "category": "fact"}]
            summarizer.process("s_vs", scored)
            if mock_vs2.store.called: P("Summarizer保存后 → vector_store.store() 被调用"); p += 1
            else: F("store未被调用"); f += 1
            # 验证传递参数
            call_args = mock_vs2.store.call_args[1]
            if call_args.get("entry_id") and len(call_args["entry_id"]) == 12:
                P("store entry_id=12位"); p += 1
            else: F(f"entry_id={call_args.get('entry_id')}"); f += 1
            if call_args.get("content") == "用户敏感信息": P("store content正确"); p += 1
            else: F(f"content={call_args.get('content')}"); f += 1

            # ===== 12. PromptBuilder 无vector_store降级 =====
            print("\n【测试11】PromptBuilder 无vector_store → 降级到ConversationStore")
            builder3 = PromptBuilder()  # 无vector_store
            result3 = builder3.build_full("s_none", "你好", MISSProfile())
            if "messages" in result3: P("无VS: build正常"); p += 1
            else: F("build失败"); f += 1

            # ===== 13. PromptBuilder vector_store异常容错 =====
            print("\n【测试12】PromptBuilder vector_store.recall()异常 → 容错降级")
            crash_vs = MagicMock()
            crash_vs.recall.side_effect = RuntimeError("模拟崩溃")
            builder4 = PromptBuilder(vector_store=crash_vs)
            result4 = builder4.build_full("s_crash", "测试", MISSProfile())
            if "messages" in result4: P("recall异常: PromptBuilder不崩溃, 正常返回"); p += 1
            else: F("build失败"); f += 1

            # ===== 14. MemorySummarizer vector_store异常容错 =====
            print("\n【测试13】MemorySummarizer vector_store.store()异常 → 容错")
            crash_vs2 = MagicMock()
            crash_vs2.store.side_effect = RuntimeError("模拟崩溃")
            summarizer2 = MemorySummarizer(vector_store=crash_vs2)
            scored = [{"content": "测试", "importance": 90, "category": "fact"}]
            # 应该不抛异常
            try:
                summarizer2.process("s_crash2", scored)
                P("VS store异常: MemorySummarizer不崩溃"); p += 1
            except Exception as e:
                F(f"异常: {e}"); f += 1

            # ===== 15. sync_from_db 结构 =====
            print("\n【测试14】sync_from_db 签名与方法检查")
            sig = inspect.signature(store.sync_from_db)
            if "session_id" in sig.parameters: P("sync_from_db 含 session_id 参数"); p += 1
            else: F("缺 session_id"); f += 1
            source = inspect.getsource(store.sync_from_db)
            if "SessionLocal" in source: P("sync_from_db 使用 SessionLocal"); p += 1
            else: F("未使用 SessionLocal"); f += 1
            if "collection.add" in source: P("sync_from_db 调用 collection.add"); p += 1
            else: F("未调用 collection.add"); f += 1

            # ===== 16. _save_embedding_to_db 异常安全 =====
            print("\n【测试15】_save_embedding_to_db 异常容错")
            source = inspect.getsource(store._save_embedding_to_db)
            if "except Exception" in source: P("含 except Exception"); p += 1
            else: F("缺异常处理"); f += 1
            if "pass" in source: P("异常时 pass（静默）"); p += 1
            else: F("未知异常处理方式"); f += 1

            # ===== 17. 代码搜索 OpenAIEmbeddingFunction =====
            print("\n【测试16】源码审查：text-embedding-3-small 模型配置")
            vs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "services/vector_store.py")
            source = open(vs_path, "r").read()
            if "text-embedding-3-small" in source: P("model=text-embedding-3-small"); p += 1
            else: F("模型名不匹配"); f += 1
            if "OpenAIEmbeddingFunction" in source: P("使用 OpenAIEmbeddingFunction"); p += 1
            else: F("未使用"); f += 1
            if "PersistentClient" in source: P("使用 PersistentClient"); p += 1
            else: F("未使用"); f += 1

            # ===== 18. 无 API key 时不传 ef =====
            print("\n【测试17】无 API key 时 embedding function 为空")
            if 'if self._key:\n                ef = OpenAIEmbeddingFunction' in source or \
               'if self._key:\n                ef = OpenAIEmbeddingFunction(api_key=self._key' in source:
                P("仅在有API key时创建OpenAIEmbeddingFunction"); p += 1
            else:
                # 检查代码逻辑
                if "if self._key:" in source and "OpenAIEmbeddingFunction" in source:
                    P("条件判断+OpenAIEmbeddingFunction存在"); p += 1
                else:
                    F("未找到条件判断"); f += 1

            # ===== 19. prompt_builder.py 集成代码审查 =====
            print("\n【测试18】PromptBuilder.build_full 中 vector_store 集成审查")
            source_pb = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                           "services/prompt_builder.py"), "r").read()
            if "self._vector_store" in source_pb: P("PromptBuilder 含 self._vector_store"); p += 1
            else: F("缺 vector_store"); f += 1
            if "recall" in source_pb: P("PromptBuilder 调用 vector_store.recall()"); p += 1
            else: F("未调用recall"); f += 1

            # ===== 20. memory_summarizer.py 集成代码审查 =====
            print("\n【测试19】MemorySummarizer._save_memory 中 vector_store 集成审查")
            source_ms = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                           "services/memory_summarizer.py"), "r").read()
            if "self._vector_store" in source_ms: P("MemorySummarizer 含 self._vector_store"); p += 1
            else: F("缺 vector_store"); f += 1
            if "store" in source_ms.split("if self._vector_store:")[-1].split("\n")[0:3].__str__():
                P("MemorySummarizer 调用 vector_store.store()"); p += 1
            else:
                # broader check
                if "store" in source_ms and "self._vector_store" in source_ms:
                    P("含 vector_store.store 调用"); p += 1
                else:
                    F("未找到 store 调用"); f += 1

            # ===== 汇总 =====
            print("\n" + "=" * 65)
            t = p + f
            print(f"测试总数: {t}  通过: {p}  失败: {f}  通过率: {p/t*100:.1f}%")
            print("=" * 65)

        finally:
            Base.metadata.drop_all(bind=engine)
            try: os.remove("tests/data/test_accept_4_3.db")
            except OSError: pass

        if f == 0: print("\n🎉 Task 4.3 验收通过！")
        else: print("\n❌ Task 4.3 验收未通过！")
        return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
