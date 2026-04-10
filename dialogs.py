"""
dialogs.py
Reusable dialogs for BatchDispatch (PySide6).

Includes:
- PasteDialog: modal dialog to paste/import raw DATA text
- ResultsDialog: shows Outreach and Delivery outputs with copy buttons
- TemplateDialog: plain-text template editor with live preview and character counter
- ConfigDialog: settings UI
- FirstRunDialog: setup wizard for initial launch
"""

from __future__ import annotations
import copy
from typing import List, Optional
import re
import os

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat, QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPlainTextEdit, QDialogButtonBox, QWidget, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QColorDialog, QLineEdit, QComboBox,
    QMessageBox, QRadioButton, QButtonGroup, QCheckBox, QFileDialog
)

# ------------------------------ TagHighlighter ------------------------------

class TagHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.tag_format = QTextCharFormat()
        self.tag_format.setForeground(QColor("#e67e22"))  # A vibrant orange color
        self.tag_pattern = re.compile(r"\[[^\]]+\]")

    def highlightBlock(self, text: str):
        for match in self.tag_pattern.finditer(text):
            start, end = match.span()
            self.setFormat(start, end - start, self.tag_format)

# ------------------------------ PasteDialog ------------------------------

class PasteDialog(QDialog):
    """Modal dialog to paste/import raw data rows."""
    def __init__(self, parent=None, helper_text: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Paste/Import Data")
        self.resize(800, 520)
        lay = QVBoxLayout(self)
        
        if helper_text:
            lbl = QLabel(helper_text)
            lbl.setWordWrap(True)
            lay.addWidget(lbl)
            
        self.text = QPlainTextEdit()
        self.text.setPlaceholderText("Paste data rows here (TSV/Excel format)...")
        lay.addWidget(self.text, 1)
        
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        lay.addWidget(bb)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        
        self.text.setFocus()

    def get_text(self) -> str:
        return self.text.toPlainText().strip()

# ------------------------------ ResultsDialog ------------------------------

class ResultsDialog(QDialog):
    """Displays generated report text with a one-click copy button."""
    def __init__(self, parent=None, title: str = "Generated Report", content: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(700, 500)
        lay = QVBoxLayout(self)

        info_lbl = QLabel("Below is your generated message. You can copy it to paste into your text or email app.")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("font-style: italic; color: gray;")
        lay.addWidget(info_lbl)
        
        self.output = QPlainTextEdit(content)
        self.output.setReadOnly(True)
        lay.addWidget(self.output)
        
        btn_lay = QHBoxLayout()
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_all)
        btn_lay.addWidget(copy_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_lay.addWidget(close_btn)
        lay.addLayout(btn_lay)

    def _copy_all(self):
        self.output.selectAll()
        self.output.copy()
        QMessageBox.information(self, "Success", "Text copied to clipboard.")

# ------------------------------ LoginDialog ------------------------------

class LoginDialog(QDialog):
    """Placeholder for future Lasagna Love website integration."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login to Lasagna Love")
        self.setFixedWidth(350)
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("<b>Connect your Account</b>"))
        lay.addWidget(QLabel("Enter your credentials to sync directly with the portal."))
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Email address")
        lay.addWidget(self.email_edit)

        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("Password")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        lay.addWidget(self.pass_edit)

        msg = QLabel("<i>Note: Direct sync is coming soon. This is currently a placeholder.</i>")
        msg.setWordWrap(True)
        lay.addWidget(msg)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

# ------------------------------ FirstRunDialog ------------------------------

class FirstRunDialog(QDialog):
    """Welcome wizard shown when no config.json is found."""
    ResultSettings = 10
    ResultContinue = 20

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to BatchDispatch")
        self.setFixedWidth(450)
        lay = QVBoxLayout(self)

        # Placeholder for Logo/Image
        logo_lay = QHBoxLayout()
        self.logo_lbl = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "resources", "lasagna-love-logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            self.logo_lbl.setPixmap(pixmap.scaled(300, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_lbl.setText("<b>Lasagna Love</b>")
        self.logo_lbl.setAlignment(Qt.AlignCenter)
        logo_lay.addWidget(self.logo_lbl)
        lay.addLayout(logo_lay)

        lay.addWidget(QLabel("<b>Welcome to BatchDispatch</b>"))
        intro_text = QLabel("Let's get started by setting up your basic profile.\n"
                            "Your name will be used to personalize outreach message templates.")
        intro_text.setWordWrap(True)
        lay.addWidget(intro_text)
        
        lay.addSpacing(20)
        
        # User Name input
        form = QHBoxLayout()
        form.addWidget(QLabel("First Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Jane")
        form.addWidget(self.name_edit)
        lay.addLayout(form)
        
        lay.addSpacing(10)
        
        self.dont_show_cb = QCheckBox("Don't show this welcome screen again")
        self.dont_show_cb.setChecked(True)
        lay.addWidget(self.dont_show_cb)
        
        lay.addSpacing(20)
        
        btn_lay = QHBoxLayout()
        btn_settings = QPushButton("Open Settings")
        btn_continue = QPushButton("Continue to Main Screen")
        btn_lay.addWidget(btn_settings)
        btn_lay.addStretch()
        btn_lay.addWidget(btn_continue)
        lay.addLayout(btn_lay)
        
        btn_settings.clicked.connect(lambda: self.done(self.ResultSettings))
        btn_continue.clicked.connect(lambda: self.done(self.ResultContinue))

# ------------------------------ TemplateDialog ------------------------------

class TemplateDialog(QDialog):
    """Editor for message templates."""
    def __init__(self, parent=None, title: str = "Edit Template", initial_text: str = "", placeholders: List[str] = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 450)
        lay = QVBoxLayout(self)
        
        lay.addWidget(QLabel("<b>Template Text:</b>"))
        self.editor = QPlainTextEdit(initial_text or "")
        self.highlighter = TagHighlighter(self.editor.document())
        lay.addWidget(self.editor, 2)
        
        self.char_label = QLabel(f"Characters: {len(self.editor.toPlainText())}")
        lay.addWidget(self.char_label)
        self.editor.textChanged.connect(lambda: self.char_label.setText(f"Characters: {len(self.editor.toPlainText())}"))
        
        if placeholders:
            lay.addWidget(QLabel("<b>Double-click to insert:</b>"))
            self.p_list = QListWidget()
            for p in placeholders:
                QListWidgetItem(f"[{p}]", self.p_list)
            self.p_list.itemDoubleClicked.connect(self._insert_placeholder)
            lay.addWidget(self.p_list, 1)

        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _insert_placeholder(self, item: QListWidgetItem):
        self.editor.insertPlainText(item.text())
        self.editor.setFocus()

    def get_text(self) -> str:
        return self.editor.toPlainText()

# ------------------------------ ConfigDialog ------------------------------

class ConfigDialog(QDialog):
    """Settings UI."""
    outreachRequested = Signal()
    deliveryRequested = Signal()

    def __init__(self, parent=None, settings: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(450)
        self._settings = copy.deepcopy(settings) if settings else {}
        
        lay = QVBoxLayout(self)

        # Name
        nl = QHBoxLayout()
        nl.addWidget(QLabel("Volunteer Name:"))
        self.name_edit = QLineEdit(self._settings.get("user_name", ""))
        nl.addWidget(self.name_edit)
        lay.addLayout(nl)

        # Format
        fl = QHBoxLayout()
        fl.addWidget(QLabel("Date Format:"))
        self.date_combo = QComboBox()
        self.date_combo.addItems(["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])
        self.date_combo.setCurrentText(self._settings.get("date_format", "MM/DD/YYYY"))
        fl.addWidget(self.date_combo)
        lay.addLayout(fl)

        # Save Path
        sl = QHBoxLayout()
        sl.addWidget(QLabel("Save Location:"))
        self.save_edit = QLineEdit(self._settings.get("save_location", ""))
        sl.addWidget(self.save_edit)
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.clicked.connect(self._browse_save_path)
        sl.addWidget(self.btn_browse)
        lay.addLayout(sl)

        # Open Folder
        folder_lay = QHBoxLayout()
        self.btn_open_folder = QPushButton("Open Save Folder")
        self.btn_open_folder.clicked.connect(self._open_save_folder)
        folder_lay.addStretch()
        folder_lay.addWidget(self.btn_open_folder)
        lay.addLayout(folder_lay)

        # Color
        cl = QHBoxLayout()
        cl.addWidget(QLabel("Highlight Color:"))
        self.current_color = self._settings.get("addr2_color", "#0d6efd")
        self.color_btn = QPushButton(self.current_color)
        self.color_btn.setStyleSheet(f"background-color: {self.current_color}; color: white;")
        self.color_btn.clicked.connect(self._pick_color)
        cl.addWidget(self.color_btn)
        cl.addStretch(1)
        lay.addLayout(cl)

        # Dark Mode
        dm_lay = QHBoxLayout()
        self.dark_mode_cb = QCheckBox("Enable Dark Mode")
        self.dark_mode_cb.setChecked(self._settings.get("dark_mode", True))
        dm_lay.addWidget(self.dark_mode_cb)
        lay.addLayout(dm_lay)
        
        # Highlights
        hl_lay = QHBoxLayout()
        self.hl_allergy_cb = QCheckBox("Highlight Allergy (YES)")
        self.hl_allergy_cb.setChecked(self._settings.get("highlight_allergy", True))
        hl_lay.addWidget(self.hl_allergy_cb)
        
        self.hl_addr2_cb = QCheckBox("Highlight Address 2")
        self.hl_addr2_cb.setChecked(self._settings.get("highlight_addr2", True))
        hl_lay.addWidget(self.hl_addr2_cb)
        lay.addLayout(hl_lay)
        
        # Resets
        reset_lay = QHBoxLayout()
        self.btn_reset_welcome = QPushButton("Reset Welcome Screen")
        self.btn_reset_welcome.clicked.connect(self._reset_welcome)
        reset_lay.addWidget(self.btn_reset_welcome)
        
        self.btn_reset_alerts = QPushButton("Reset Name Alert Banner")
        self.btn_reset_alerts.clicked.connect(self._reset_alerts)
        reset_lay.addWidget(self.btn_reset_alerts)
        lay.addLayout(reset_lay)

        lay.addSpacing(10)
        self.btn_o = QPushButton("Edit Outreach Template…")
        self.btn_d = QPushButton("Edit Delivery Template…")
        self.btn_o.clicked.connect(self.outreachRequested.emit)
        self.btn_d.clicked.connect(self.deliveryRequested.emit)
        lay.addWidget(self.btn_o)
        lay.addWidget(self.btn_d)

        self.bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.bb.accepted.connect(self.accept)
        self.bb.rejected.connect(self.reject)
        lay.addWidget(self.bb)

    def _pick_color(self):
        col = QColorDialog.getColor(QColor(self.current_color), self, "Pick color")
        if col.isValid():
            self.current_color = col.name()
            self.color_btn.setText(self.current_color)
            self.color_btn.setStyleSheet(f"background-color: {self.current_color}; color: white;")

    def _browse_save_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Save Directory", self.save_edit.text())
        if path:
            self.save_edit.setText(path)

    def _open_save_folder(self):
        path = self.save_edit.text()
        if path and os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.warning(self, "Folder Not Found", 
                                "The specified save folder does not exist or hasn't been set yet. "
                                "Please browse for a valid folder and save your settings.")

    def updated_settings(self) -> dict:
        self._settings["user_name"] = self.name_edit.text().strip()
        self._settings["date_format"] = self.date_combo.currentText()
        self._settings["save_location"] = self.save_edit.text().strip()
        self._settings["addr2_color"] = self.current_color
        self._settings["dark_mode"] = self.dark_mode_cb.isChecked()
        self._settings["highlight_allergy"] = self.hl_allergy_cb.isChecked()
        self._settings["highlight_addr2"] = self.hl_addr2_cb.isChecked()
        return self._settings
        
    def _reset_welcome(self):
        self._settings["show_welcome_screen"] = True
        QMessageBox.information(self, "Reset", "Welcome screen reset. Please click OK to save changes.")
        
    def _reset_alerts(self):
        self._settings["show_name_alert"] = True
        QMessageBox.information(self, "Reset", "Alert banners reset. Please click OK to save changes.")