"""
models.py
Qt models/delegates for LASER Desktop.
"""

from __future__ import annotations
import pandas as pd
from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtGui import QColor

# ... (DISPLAY_LABELS and LASER_COLUMNS_ORDER constants remain the same) ...

class TrackingModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame = None, settings: dict = None):
        super().__init__()
        self._df = df if df is not None else pd.DataFrame()
        self.settings = settings or {}
        self._default_allergy_color = QColor("#ff4d4f")
        self._default_addr2_color = QColor("#0d6efd")

    def rowCount(self, parent=None): 
        if parent is not None and parent.isValid(): return 0
        return len(self._df)
        
    def columnCount(self, parent=None): 
        if parent is not None and parent.isValid(): return 0
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid(): return None
        row, col = index.row(), index.column()
        val = self._df.iat[row, col]
        colname = self._df.columns[col]
        
        if role == Qt.CheckStateRole and colname == "Select":
            return Qt.Checked if val is True else Qt.Unchecked

        if role in (Qt.DisplayRole, Qt.EditRole):
            if colname == "Select":
                return None
            return str(val) if pd.notna(val) else ""
            
        if role == Qt.BackgroundRole:
            if self.settings.get("highlight_allergy", True):
                allergy_cols = ["Gluten-Free", "Dairy-Free", "Nut Allergy", "Other Allergy"]
                if colname in allergy_cols and str(val).strip().upper() == "YES":
                    return QColor(self.settings.get("allergy_color", self._default_allergy_color))
                    
        if role == Qt.ForegroundRole:
            if self.settings.get("highlight_addr2", True):
                if colname == "Address 2" and pd.notna(val) and str(val).strip():
                    return QColor(self.settings.get("addr2_color", self._default_addr2_color))
                    
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section < len(self._df.columns):
                return str(self._df.columns[section])
        return super().headerData(section, orientation, role)

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid(): return False
        
        row, col = index.row(), index.column()
        colname = self._df.columns[col]

        if role == Qt.CheckStateRole and colname == "Select":
            self._df.iat[row, col] = (value == Qt.Checked or value == Qt.Checked.value)
            self.dataChanged.emit(index, index, [Qt.CheckStateRole])
            return True

        if role != Qt.EditRole: return False

        try:
            if colname == "Deliverystoporder":
                if not str(value).strip():
                    self._df.iat[row, col] = pd.NA
                else:
                    val = int(float(value))
                    if val < 1: return False
                    self._df.iat[row, col] = val
            else:
                self._df.iat[row, col] = value

            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])

            return True
        except Exception:
            return False

    def flags(self, index):
        if not index.isValid(): return Qt.NoItemFlags
        colname = self._df.columns[index.column()]
        base_flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        
        if colname == "Select":
            return base_flags | Qt.ItemIsUserCheckable
            
        return base_flags | Qt.ItemIsEditable