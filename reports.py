"""
reports.py
Report-generation and validation helpers for BatchDispatch.
"""

from __future__ import annotations
import datetime as dt
from pathlib import Path
from typing import List, Optional
import re

import pandas as pd

# ------------------------------ Outreach ------------------------------

def _apply_computed_tags(text: str, row: pd.Series) -> str:
    """Helper to handle virtual tags like [fullname] and [fulladdress]."""
    # Full Name
    fname = str(row.get("First Name", "")).strip()
    lname = str(row.get("Last Name", "")).strip()
    text = text.replace("[fullname]", f"{fname} {lname}".strip())
    
    # Full Address
    addr1 = str(row.get("Address 1", "")).strip()
    addr2 = str(row.get("Address 2", "")).strip()
    city = str(row.get("City", "")).strip()
    zip_val = str(row.get("Zip", "")).strip()
    full_addr = f"{addr1} {addr2}, {city} {zip_val}".replace(" ,", ",").strip()
    text = text.replace("[fulladdress]", full_addr)
    
    # Contact Phone
    text = text.replace("[contactphone]", str(row.get("Phone number", "")))
    
    # Allergy Flag
    allergy_cols = ["Gluten-Free", "Dairy-Free", "Nut Allergy", "Other Allergy"]
    has_allergy = any(str(row.get(col, "")).strip().upper() == "YES" for col in allergy_cols)
    text = text.replace("[allergyflag]", "!! ALLERGY !!" if has_allergy else "None")
    
    return text

def build_outreach_text(df: pd.DataFrame, template_text: str, user_name: str, custom_tags: dict = None) -> str:
    """Render Outreach text with [placeholders] replaced by field values."""
    custom_tags = custom_tags or {}
    msgs: List[str] = []
    for _, row in df.iterrows():
        text = template_text
        # Use simple string replacement instead of re.sub to avoid escape-character crashes
        for k, v in row.items():
            placeholder = f"[{k}]"
            if pd.notna(v):
                val = str(int(v)) if isinstance(v, float) and v.is_integer() else str(v)
            else:
                val = ""
            text = text.replace(placeholder, val)
            
        for tag, field in (custom_tags or {}).items():
            raw_val = row.get(field)
            if pd.notna(raw_val):
                val = str(int(raw_val)) if isinstance(raw_val, float) and raw_val.is_integer() else str(raw_val)
            else:
                val = ""
            text = text.replace(f"[{tag}]", val)
        
        text = text.replace("[user]", user_name or "")
        text = text.replace("[MyName]", user_name or "")
        text = _apply_computed_tags(text, row)
        msgs.append(text)
    return "\n\n".join(msgs)


# ------------------------------ Delivery ------------------------------

def build_delivery_text(df: pd.DataFrame, template_text: str, user_name: str, custom_tags: dict = None) -> str:
    """Render Delivery report text block for drivers."""
    custom_tags = custom_tags or {}
    blocks: List[str] = []
    # Sort by delivery order if available
    work_df = df.copy()
    if "Deliverystoporder" in work_df.columns:
        work_df["Deliverystoporder"] = pd.to_numeric(work_df["Deliverystoporder"], errors='coerce').fillna(999)
        work_df = work_df.sort_values("Deliverystoporder")

    for _, row in work_df.iterrows():
        text = template_text
        row_dict = row.to_dict()
        
        for k, v in row_dict.items():
            placeholder = f"[{k}]"
            if pd.notna(v):
                val = str(int(v)) if isinstance(v, float) and v.is_integer() else str(v)
            else:
                val = ""
            text = text.replace(placeholder, val)
            
        for tag, field in custom_tags.items():
            raw_val = row_dict.get(field)
            if pd.notna(raw_val):
                val = str(int(raw_val)) if isinstance(raw_val, float) and raw_val.is_integer() else str(raw_val)
            else:
                val = ""
            text = text.replace(f"[{tag}]", val)
            
        text = text.replace("[user]", user_name or "")
        text = text.replace("[MyName]", user_name or "")
        text = _apply_computed_tags(text, row)
        text += f"\n{'-'*40}"
        blocks.append(text)
    return "\n\n".join(blocks)


# ------------------------------ Validation ------------------------------

def validate_delivery_order_consecutive(df: pd.DataFrame) -> Optional[str]:
    """Check that Deliverystoporder values are valid unique integers."""
    if "Deliverystoporder" not in df.columns:
        return "Missing 'Delivery Order' column."
    
    if df["Deliverystoporder"].isna().any():
        return "Some selected rows have an empty Delivery Order."
        
    orders = df["Deliverystoporder"].astype(str).str.strip()
    if orders.eq("").any() or orders.eq("nan").any() or orders.eq("<NA>").any():
        return "Some selected rows have an empty Delivery Order."
    
    try:
        nums = [int(float(n)) for n in orders if n]
    except ValueError:
        return "Delivery Order must contain only whole numbers."
    
    if len(nums) != len(set(nums)):
        return "Duplicate Delivery Order numbers detected."
    
    if any(n < 1 for n in nums):
        return "Delivery Order numbers must be 1 or greater."
        
    return None

def save_reports(outreach_text: str, delivery_text: str, export_dir: Path, user_name: str):
    """Save outreach/delivery text files."""
    export_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now()
    
    if outreach_text:
        path = export_dir / f"Outreach_{ts:%Y%m%d_%H%M%S}.txt"
        path.write_text(outreach_text, encoding="utf-8")
        
    if delivery_text:
        # Sanitize name for filesystem safety
        safe_name = re.sub(r'[\\/*?:"<>|]', "", user_name or "User").replace(" ", "_")
        path = export_dir / f"Delivery_{safe_name}_{ts:%Y%m%d}.txt"
        path.write_text(delivery_text, encoding="utf-8")