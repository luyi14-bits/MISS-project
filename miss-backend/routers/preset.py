import json
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from limiter import limiter
from database import SessionLocal
from models.preset import Preset
from services.attribute_engine import MISSProfile


class SavePresetRequest(BaseModel):
    name: str = Field(default="未命名预设", max_length=100)
    profile: MISSProfile = MISSProfile()
    background: str = Field(default="", max_length=5000)


class ApplyPresetRequest(BaseModel):
    preset_id: str


router = APIRouter()


@router.get("/preset/list")
@limiter.limit("30/minute")
async def list_presets(request: Request):
    db = SessionLocal()
    try:
        rows = db.query(Preset).order_by(Preset.created_at.desc()).all()
        return {
            "presets": [
                {
                    "id": r.id,
                    "name": r.name,
                    "profile": json.loads(r.profile_json),
                    "background": r.background or "",
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
        }
    finally:
        db.close()


@router.post("/preset/save")
@limiter.limit("10/minute")
async def save_preset(request: Request, req: SavePresetRequest):
    preset_id = uuid.uuid4().hex[:12]
    db = SessionLocal()
    try:
        preset = Preset(
            id=preset_id,
            name=req.name,
            profile_json=req.profile.model_dump_json(),
            background=req.background,
            created_at=datetime.now(timezone.utc),
        )
        db.add(preset)
        db.commit()
        return {"id": preset_id, "name": req.name, "background": req.background, "message": "预设已保存"}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.get("/preset/{preset_id}")
@limiter.limit("30/minute")
async def get_preset(request: Request, preset_id: str):
    db = SessionLocal()
    try:
        preset = db.query(Preset).filter(Preset.id == preset_id).first()
        if not preset:
            raise HTTPException(status_code=404, detail="预设不存在")
        return {
            "id": preset.id,
            "name": preset.name,
            "profile": json.loads(preset.profile_json),
            "background": preset.background or "",
            "created_at": preset.created_at.isoformat() if preset.created_at else None,
        }
    finally:
        db.close()


@router.delete("/preset/{preset_id}")
@limiter.limit("10/minute")
async def delete_preset(request: Request, preset_id: str):
    db = SessionLocal()
    try:
        preset = db.query(Preset).filter(Preset.id == preset_id).first()
        if not preset:
            raise HTTPException(status_code=404, detail="预设不存在")
        db.delete(preset)
        db.commit()
        return {"message": "预设已删除"}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/preset/apply")
@limiter.limit("10/minute")
async def apply_preset(request: Request, req: ApplyPresetRequest):
    db = SessionLocal()
    try:
        preset = db.query(Preset).filter(Preset.id == req.preset_id).first()
        if not preset:
            raise HTTPException(status_code=404, detail="预设不存在")
        try:
            profile = MISSProfile.model_validate_json(preset.profile_json)
        except Exception:
            raise HTTPException(status_code=422, detail="预设数据损坏，无法应用")
        return {
            "message": "预设已应用",
            "profile": profile.model_dump(),
            "background": preset.background or "",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"应用预设失败：{str(e)}")
    finally:
        db.close()


@router.get("/preset/{preset_id}/export")
@limiter.limit("10/minute")
async def export_preset(request: Request, preset_id: str):
    db = SessionLocal()
    try:
        preset = db.query(Preset).filter(Preset.id == preset_id).first()
        if not preset:
            raise HTTPException(status_code=404, detail="预设不存在")
        profile = json.loads(preset.profile_json)
        easter_egg_hint = _detect_easter_egg_hint(profile)
        export_data = {
            "version": "1.1",
            "name": preset.name,
            "profile": profile,
            "background": preset.background or "",
            "easter_egg_hint": easter_egg_hint,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }
        return JSONResponse(
            content=export_data,
            headers={
                "Content-Disposition": f'attachment; filename="miss_preset_{preset_id}.json"'
            },
        )
    finally:
        db.close()


@router.post("/preset/import")
@limiter.limit("5/minute")
async def import_preset(request: Request, file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="请上传 .json 文件")

    raw = await file.read()
    MAX_FILE_SIZE = 1024 * 1024
    if len(raw) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件过大（上限 1MB）")

    try:
        data = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="JSON 文件格式无效")

    if "profile" not in data:
        raise HTTPException(status_code=400, detail="缺少必需字段 profile")

    profile_data = data["profile"]
    if not isinstance(profile_data, dict):
        raise HTTPException(status_code=400, detail="profile 必须是对象")

    name = str(data.get("name", f"导入_{file.filename.replace('.json', '')}"))[:100]
    background = str(data.get("background", ""))[:5000]

    try:
        MISSProfile.model_validate(profile_data)
    except Exception:
        raise HTTPException(status_code=400, detail="profile 格式不符合 MISSProfile 规范")

    preset_id = uuid.uuid4().hex[:12]
    db = SessionLocal()
    try:
        preset = Preset(
            id=preset_id,
            name=name,
            profile_json=json.dumps(profile_data, ensure_ascii=False),
            background=background,
            created_at=datetime.now(timezone.utc),
        )
        db.add(preset)
        db.commit()
        return {
            "id": preset_id,
            "name": name,
            "profile": profile_data,
            "background": background,
            "message": "预设已导入",
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _detect_easter_egg_hint(profile: dict) -> str | None:
    edu = profile.get("education_level", 0)
    hints = []
    if edu == -100:
        hints.append("⚠ 教育水平 = -100 → ⑨模式（BAKA~）已激活")
    elif edu <= -90:
        hints.append("💡 教育水平接近 -100，再降一点就会触发⑨彩蛋")
    elif edu <= -70:
        hints.append("📘 当前为低文化水平模式")

    return "；".join(hints) if hints else None
