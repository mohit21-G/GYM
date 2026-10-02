"""
hydration_service.py
---------------------
Small helper service for hydration logs, mirroring the sync-to-conversation
pattern already used by FoodService.sync_food_log_to_conversation_messages.

Hydration cards are embedded in chat_service.py responses as either:
  - a single-item CREATE_HYDRATION_LOG card: data.entries = [{id, time, amountMl, beverageName}]
  - a multi-log hydration card: data.entries = [{id, time, amountMl, beverageName, loggedAt}, ...]

Both shapes are persisted into conversation_messages.raw_entities (the chat
"ui" payload). When a hydration log is edited or deleted via the API, this
sync function keeps that persisted history in sync so a page refresh/session
reload doesn't show stale amounts.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from ..database import get_db


class HydrationService:
    @staticmethod
    async def sync_hydration_log_to_conversation_messages(
        user_id: str,
        log_id: str,
        updated_entry: Optional[Dict[str, Any]] = None,
        is_deleted: bool = False,
    ) -> None:
        """Update or remove a hydration entry inside any persisted chat message
        that embedded it, so session reload reflects the current DB state."""
        db = get_db()
        cursor = db.conversation_messages.find({"raw_entities": {"$ne": None}})
        messages = await cursor.to_list(length=500)

        for m in messages:
            raw_ent = m.get("raw_entities")
            if not isinstance(raw_ent, dict):
                continue

            # Hydration entries can live either directly under raw_ent["entries"]
            # (single-card shape) or inside one of raw_ent["cards"][i]["entries"]
            # (multi-log shape). Handle both.
            modified = False

            def _patch_entries(entries):
                nonlocal modified
                new_list = []
                changed = False
                for e in entries or []:
                    if str(e.get("id") or "") == str(log_id):
                        changed = True
                        if is_deleted:
                            continue
                        if updated_entry:
                            h_cal = float(updated_entry.get("calories") or 0.0)
                            new_list.append({
                                **e,
                                "amountMl": int(updated_entry.get("amount_ml", e.get("amountMl", 0))),
                                "beverageName": updated_entry.get("beverage_name", e.get("beverageName")),
                                "quantity": updated_entry.get("quantity"),
                                "calories": h_cal if h_cal > 0 else None,
                                "proteinG": float(updated_entry.get("protein_g") or 0.0) if h_cal > 0 else None,
                                "carbsG": float(updated_entry.get("carbs_g") or 0.0) if h_cal > 0 else None,
                                "fatG": float(updated_entry.get("fat_g") or 0.0) if h_cal > 0 else None,
                                "fiberG": float(updated_entry.get("fiber_g") or 0.0) if h_cal > 0 else None,
                            })
                        else:
                            new_list.append(e)
                    else:
                        new_list.append(e)
                if changed:
                    modified = True
                return new_list

            if isinstance(raw_ent.get("entries"), list):
                raw_ent["entries"] = _patch_entries(raw_ent["entries"])

            cards = raw_ent.get("cards")
            if isinstance(cards, list):
                for card in cards:
                    if isinstance(card, dict) and isinstance(card.get("entries"), list):
                        card["entries"] = _patch_entries(card["entries"])

            if modified:
                await db.conversation_messages.update_one(
                    {"id": m["id"]},
                    {"$set": {"raw_entities": raw_ent}},
                )
