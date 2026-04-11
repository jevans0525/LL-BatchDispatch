"""
parsing.py
Utilities for robust LASER DATA paste/import handling.
"""

from __future__ import annotations
from typing import List, Tuple
import pandas as pd

VERSION = "1.0.0"

# ------------------------------ Canonical headers ------------------------------

CANONICAL_DATA_HEADERS: List[str] = [
    "Actions", "Status", "Scheduled", "Delivered", "First Name", 
    "Last Name", "Phone number", "Email", "Address 1", "Address 2", 
    "City", "State", "Zip", "Country", "Family Size", "Gluten-Free", 
    "Dairy-Free", "Nut Allergy", "Other Allergy"
]
HEADER_SET = {h.lower() for h in CANONICAL_DATA_HEADERS}

# ------------------------------ Parsing Core ------------------------------

def map_headerless(df: pd.DataFrame) -> pd.DataFrame:
    if df.shape[1] < 19:
        raise ValueError("Headerless paste must include at least the first 19 columns.")
    n = min(df.shape[1], len(CANONICAL_DATA_HEADERS))
    df = df.iloc[:, :n]
    df.columns = CANONICAL_DATA_HEADERS[:n]
    return df

def detect_headers(df: pd.DataFrame) -> bool:
    """True if the first row has matching header values."""
    if df.empty:
        return False
    first_row = [str(x).strip().lower() for x in df.iloc[0].tolist()]
    if "email" in first_row:
        return True
    matches = sum(1 for h in first_row if h in HEADER_SET)
    return matches >= 5

def coerce_headers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure DataFrame has proper headers.
    FIX: Rely on pandas internal types rather than string casting.
    """
    # Safe check for default integer headers (e.g. pandas loaded a file with header=None)
    if isinstance(df.columns, pd.RangeIndex) or all(str(c).isdigit() for c in df.columns):
        if detect_headers(df):
            # Promote the first row to headers
            df.columns = [str(x).strip() for x in df.iloc[0].tolist()]
            df = df.drop(df.index[0]).reset_index(drop=True)
            return df
        # Fallback map for pure data with no headers at all
        return map_headerless(df)
        
    # Standardize string headers
    df.columns = [str(c).strip() for c in df.columns]
    return df

def basic_validate_email_id(df: pd.DataFrame) -> Tuple[int, int]:
    """Validate that required columns exist and report invalid email count."""
    missing = 0
    if "Email" not in df.columns:
        missing += 1
            
    invalid_emails = 0
    if "Email" in df.columns:
        invalid_emails = df["Email"].isna().sum()
        
    return missing, invalid_emails