# app.py
# BatchDispatch
# Main application entrypoint.

from __future__ import annotations
import sys
import json
import re
import shutil
import io
import urllib.request
import logging
import traceback
import pandas as pd
import datetime as dt
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QDialog, QVBoxLayout, 
    QLabel, QPushButton, QHBoxLayout, QTableView, QWidget, QAbstractItemView,
    QDockWidget, QPlainTextEdit, QComboBox, QLineEdit, QCheckBox, QStyledItemDelegate,
    QStyle, QStyleOptionViewItem,
    QListWidget, QListWidgetItem, QFormLayout, QDialogButtonBox, QMenu, QFileDialog, QInputDialog
)
from PySide6.QtGui import (
    QKeySequence, QShortcut, QPalette, QColor, QAction, QCursor, QDesktopServices,
    QSyntaxHighlighter, QTextCharFormat, QTextDocument, QAbstractTextDocumentLayout, QPixmap, QIcon
)
from PySide6.QtCore import Qt, QTimer, QUrl, QSortFilterProxyModel, Signal

# Ensure these modules are in the same folder
from dialogs import ConfigDialog, FirstRunDialog, TemplateDialog, ResultsDialog, TagHighlighter, LoginDialog
from models import TrackingModel
import parsing
import reports

APP_DIR = Path.home() / ".batch_dispatch_app"
RESOURCES_DIR = Path(__file__).parent / "resources"
CONFIG_PATH = APP_DIR / "config.json"
DOCS_DIR = Path.home() / "Documents" / "BatchDispatch"
TEMPLATES_DIR = DOCS_DIR / "templates"
BUNDLED_TEMPLATES_DIR = RESOURCES_DIR / "templates"
LOG_PATH = APP_DIR / "app.log"

def setup_logging():
    """Configures the logging system."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        encoding="utf-8"
    )

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler to log crashes and notify the user."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.critical("Unhandled exception occurred:\n%s", error_msg)

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle("Application Error")
    msg.setText("An unhandled exception occurred.")
    msg.setInformativeText(str(exc_value))
    msg.setDetailedText(error_msg)
    msg.exec()

class ImportDialog(QDialog):
    def __init__(self, parent=None, settings: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Import Data Review")
        self.resize(800, 600)
        self.settings = settings or {}
        
        self.empty_df = pd.DataFrame(columns=["Select"] + parsing.CANONICAL_DATA_HEADERS)
        self.model = TrackingModel(self.empty_df.copy(), self.settings)
        self.imported_df = None
        
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        layout = QVBoxLayout(self)
        self.info_label = QLabel("Press Ctrl+V (or Cmd+V) to paste data.")
        self.info_label.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.info_label)
        layout.addWidget(self.table_view)
        
        self.btn_layout = QHBoxLayout()
        self.btn_clear = QPushButton("Clear Data")
        self.btn_accept = QPushButton("Accept Data")
        self.btn_layout.addWidget(self.btn_clear)
        self.btn_layout.addWidget(self.btn_accept)
        layout.addLayout(self.btn_layout)
        
        self.btn_accept.clicked.connect(self.accept_data)
        self.btn_clear.clicked.connect(self.clear_data)
        self.btn_accept.setEnabled(False)
        self.btn_clear.setEnabled(False)

        paste_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Paste), self)
        paste_shortcut.activated.connect(self.paste_data)

    def paste_data(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text: return
        try:
            buffer = io.StringIO(text)
            # Try to detect if it's tab or comma separated
            first_line = text.split('\n')[0]
            separator = '\t' if '\t' in first_line else ','
            
            buffer.seek(0)
            raw_df = pd.read_csv(buffer, sep=separator, header=None)
            if raw_df.empty:
                raise ValueError("The clipboard appears to be empty or contains no valid data.")
            df = parsing.coerce_headers(raw_df)
            if "Select" not in df.columns:
                df.insert(0, "Select", True)
            self.model.beginResetModel()
            self.model._df = df
            self.model.endResetModel()
            logging.info(f"Successfully pasted {len(df)} rows into ImportDialog.")
            self.info_label.setText(f"Loaded {len(df)} rows from clipboard. Please review and accept.")
            self.btn_accept.setEnabled(True)
            self.btn_clear.setEnabled(True)
        except Exception as e:
            logging.error(f"Failed to parse pasted data: {e}", exc_info=True)
            QMessageBox.warning(self, "Paste Error", f"Failed to parse pasted data:\n{e}")

    def accept_data(self):
        self.imported_df = self.model._df.copy()
        self.accept()

    def clear_data(self):
        self.model.beginResetModel()
        self.model._df = self.empty_df.copy()
        self.model.endResetModel()
        self.info_label.setText("Press Ctrl+V (or Cmd+V) to paste data.")
        self.btn_accept.setEnabled(False)
        self.btn_clear.setEnabled(False)

class FilterProxyModel(QSortFilterProxyModel):
    """Filters tracking data by name or address across multiple columns."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_text = ""

    def setFilterString(self, text: str):
        self.filter_text = text.lower().strip()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent):
        if not self.filter_text:
            return True
        model = self.sourceModel()
        df = model._df
        # Match against name and address fields specifically
        search_cols = ["First Name", "Last Name", "Address 1", "Address 2", "City", "Phone number"]
        for col in search_cols:
            if col in df.columns:
                if self.filter_text in str(df.iloc[source_row][col]).lower():
                    return True
        return False

class HighlightDelegate(QStyledItemDelegate):
    """Draws table cells with highlighted search terms."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_text = ""
        self._doc = QTextDocument()  # Reuse document instance

    def set_filter_text(self, text: str):
        self.filter_text = text

    def paint(self, painter, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        # Only highlight text-based columns, skip things like the checkbox column
        header = index.model().headerData(index.column(), Qt.Horizontal)
        if not self.filter_text or header == "Select" or not options.text:
            super().paint(painter, option, index)
            return

        # Escape HTML and inject highlighting span
        display_text = options.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if self.filter_text.lower() in display_text.lower():
            painter.save()
            self._doc.setDefaultFont(options.font)
            pattern = re.compile(re.escape(self.filter_text), re.IGNORECASE)
            highlighted = pattern.sub(r'<b><span style="background-color: #ff9800; color: black;">\g<0></span></b>', display_text)
            self._doc.setHtml(highlighted)
        
            options.text = ""
            option.widget.style().drawControl(QStyle.CE_ItemViewItem, options, painter)
            text_rect = option.widget.style().subElementRect(QStyle.SE_ItemViewItemText, options)
            painter.translate(text_rect.topLeft())
            self._doc.drawContents(painter)
            painter.restore()
        else:
            super().paint(painter, option, index)

class MainWindow(QMainWindow):
    update_detected = Signal(str, str) # version, download_url

    def __init__(self, settings: dict):
        super().__init__()
        self.setWindowTitle("BatchDispatch")
        self.setWindowIcon(QIcon(str(RESOURCES_DIR / "heart-1.png")))
        self.resize(1024, 768)
        self.settings = settings
        self.is_authenticated = False # Future state
        self.user_token = None        # Future session token
        self.row_undo_stack = []
        self.statusBar().showMessage("Ready")
        
        # Initialize the model with local settings
        self.empty_df = pd.DataFrame(columns=["Select"] + parsing.CANONICAL_DATA_HEADERS)
        self.model = TrackingModel(self.empty_df.copy(), self.settings)
        
        self.proxy_model = FilterProxyModel()
        self.proxy_model.setSourceModel(self.model)

        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)

        self.highlight_delegate = HighlightDelegate(self.table_view)
        self.table_view.setItemDelegate(self.highlight_delegate)
        self.table_view.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed | QAbstractItemView.AnyKeyPressed)
        self.table_view.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.horizontalHeader().customContextMenuRequested.connect(self.show_column_menu)
        
        # Hide columns not in the requested visible list by default
        visible_cols = {
            "Select", "First Name", "Last Name", "Phone number", "Email",
            "Address 1", "Address 2", "City", "State", "Zip",
            "Family Size", "Gluten-Free", "Dairy-Free", "Nut Allergy", "Other Allergy"
        }
        for i in range(self.model.columnCount()):
            header = self.model.headerData(i, Qt.Horizontal)
            if header not in visible_cols:
                self.table_view.setColumnHidden(i, True)

        layout = QVBoxLayout()
        
        self.banner_widget = QWidget()
        banner_layout = QHBoxLayout(self.banner_widget)
        banner_layout.setContentsMargins(5, 5, 5, 5)
        self.banner_label = QLabel("Please set your Volunteer Name in Settings.")
        self.banner_label.setStyleSheet("color: white; font-weight: bold;")
        self.banner_widget.setStyleSheet("background-color: #ff9800; border-radius: 4px;")
        
        btn_open_settings = QPushButton("Open Settings")
        btn_open_settings.clicked.connect(self.open_settings)
        btn_open_settings.setStyleSheet("background-color: white; color: black; border-radius: 2px; padding: 4px;")
        
        self.banner_dont_show = QCheckBox("Don't show this again")
        self.banner_dont_show.setStyleSheet("color: white;")
        self.banner_dont_show.stateChanged.connect(self.hide_banner_permanently)
        
        banner_layout.addWidget(self.banner_label)
        banner_layout.addWidget(btn_open_settings)
        banner_layout.addWidget(self.banner_dont_show)
        layout.addWidget(self.banner_widget)
        
        top_layout = QHBoxLayout()
        self.btn_import = QPushButton("Import Data")
        self.btn_import.clicked.connect(self.open_import_dialog)
        self.btn_import.setToolTip("Click here to paste data from your spreadsheet or the Lasagna Love portal.")
        top_layout.addWidget(self.btn_import)

        self.btn_settings = QPushButton("Settings")
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_settings.setToolTip("Change your name, date formats, or app colors.")
        top_layout.addWidget(self.btn_settings)

        self.btn_toggle_dock = QPushButton("Toggle Template Editor")
        self.btn_toggle_dock.setCheckable(True)
        self.btn_toggle_dock.setToolTip("Show or hide the message writing area at the bottom.")
        self.btn_toggle_dock.setChecked(self.settings.get("show_docked_editor", False))
        self.btn_toggle_dock.toggled.connect(self.toggle_dock)
        top_layout.addWidget(self.btn_toggle_dock)

        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.setToolTip("Check all boxes in the 'Select' column.")
        self.btn_select_all.clicked.connect(self.select_all_rows)
        top_layout.addWidget(self.btn_select_all)

        self.btn_deselect_all = QPushButton("Deselect All")
        self.btn_deselect_all.setToolTip("Uncheck all boxes in the 'Select' column.")
        self.btn_deselect_all.clicked.connect(self.deselect_all_rows)
        top_layout.addWidget(self.btn_deselect_all)

        top_layout.addSpacing(20)
        top_layout.addWidget(QLabel("Filter:"))
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search name or address...")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.setFixedWidth(200)
        self.search_bar.textChanged.connect(self.update_search)
        top_layout.addWidget(self.search_bar)

        # Search Shortcut (Ctrl+F)
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.search_bar.setFocus)

        top_layout.addStretch()

        # Heart Icon in Top Right
        heart_label = QLabel()
        heart_pixmap = QPixmap(str(RESOURCES_DIR / "heart-1.png"))
        if not heart_pixmap.isNull():
            heart_label.setPixmap(heart_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        top_layout.addWidget(heart_label)
        
        layout.addLayout(top_layout)
        layout.addWidget(self.table_view)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        self.dock = QDockWidget("Template Editor", self)
        self.dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        dock_container = QWidget()
        dock_layout = QHBoxLayout(dock_container)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.tag_list = QListWidget()
        self.populate_tags()
        
        btn_create_tag = QPushButton("Create Tag")
        btn_create_tag.clicked.connect(self.create_tag)
        btn_insert_tag = QPushButton("Insert Tag")
        btn_insert_tag.clicked.connect(self.insert_tag)
        btn_remove_tag = QPushButton("Remove Tag")
        btn_remove_tag.clicked.connect(self.remove_tag)
        
        left_layout.addWidget(QLabel("Available Tags:"))
        left_layout.addWidget(self.tag_list)
        left_layout.addWidget(btn_create_tag)
        btn_insert_tag.setToolTip("Add the selected tag into your message at the cursor position.")
        left_layout.addWidget(btn_insert_tag)
        left_layout.addWidget(btn_remove_tag)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        top_right_layout = QHBoxLayout()
        
        self.btn_undo_menu = QPushButton("Undo History")
        self.btn_undo_menu.clicked.connect(self.show_undo_menu)
        
        top_right_layout.addStretch()
        top_right_layout.addWidget(self.btn_undo_menu)
        
        self.dock_editor = QPlainTextEdit()
        self.dock_highlighter = TagHighlighter(self.dock_editor.document())
        self.undo_stack = []
        self.undo_timer = QTimer(self)
        self.undo_timer.setSingleShot(True)
        self.undo_timer.setInterval(1000)
        self.undo_timer.timeout.connect(self._commit_undo_snapshot)
        self.dock_editor.textChanged.connect(self.undo_timer.start)
        
        bottom_right_layout = QHBoxLayout()
        self.dock_save_btn = QPushButton("Save Template")
        self.dock_save_btn.clicked.connect(self.save_dock_template)
        
        self.dock_save_generate_btn = QPushButton("Save and Generate")
        self.dock_save_generate_btn.clicked.connect(self.save_and_generate)
        
        bottom_right_layout.addWidget(self.dock_save_btn)
        bottom_right_layout.addWidget(self.dock_save_generate_btn)
        
        right_layout.addLayout(top_right_layout)
        right_layout.addWidget(self.dock_editor)
        right_layout.addLayout(bottom_right_layout)
        
        dock_layout.addWidget(left_panel, 1)
        dock_layout.addWidget(right_panel, 3)
        
        far_right_panel = QWidget()
        far_right_layout = QVBoxLayout(far_right_panel)
        
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self.load_dock_template)
        
        btn_new_template = QPushButton("Create New Template")
        btn_new_template.clicked.connect(self.create_template)
        btn_import_template = QPushButton("Import Template")
        btn_import_template.clicked.connect(self.import_template)
        btn_remove_template = QPushButton("Remove Template")
        btn_remove_template.clicked.connect(self.remove_template)
        
        far_right_layout.addWidget(QLabel("Saved Templates:"))
        far_right_layout.addWidget(self.template_list)
        far_right_layout.addWidget(btn_new_template)
        far_right_layout.addWidget(btn_import_template)
        far_right_layout.addWidget(btn_remove_template)
        
        dock_layout.addWidget(far_right_panel, 1)
        
        self.dock.setWidget(dock_container)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock)
        self.dock.setVisible(self.settings.get("show_docked_editor", False))
        self.populate_templates()
        self._setup_menus()
        
        self.apply_dark_mode(self.settings.get("dark_mode", True))
        self.check_banner()

    def _setup_menus(self):
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        import_action = QAction("&Import Data...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.open_import_dialog)
        file_menu.addAction(import_action)
        
        clear_action = QAction("&Clear Selected Rows", self)
        clear_action.setShortcut(QKeySequence.StandardKey.Delete)
        clear_action.triggered.connect(self.clear_selected_rows)
        file_menu.addAction(clear_action)

        self.undo_delete_action = QAction("&Undo Delete Rows", self)
        self.undo_delete_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_delete_action.triggered.connect(self.undo_clear_rows)
        self.undo_delete_action.setEnabled(False)
        file_menu.addAction(self.undo_delete_action)

        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        doc_action = QAction("&Documentation", self)
        doc_action.triggered.connect(self.open_documentation)
        help_menu.addAction(doc_action)
        
        website_action = QAction("&Visit Lasagna Love", self)
        website_action.triggered.connect(self.open_website)
        help_menu.addAction(website_action)
        
        report_action = QAction("&Report a Bug / Feedback...", self)
        report_action.triggered.connect(self.report_bug)
        help_menu.addAction(report_action)

        update_action = QAction("Check for Updates...", self)
        update_action.triggered.connect(lambda: self.check_for_updates(manual=True))
        help_menu.addAction(update_action)

        help_menu.addSeparator()
        
        about_action = QAction("&About BatchDispatch", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def handle_login(self):
        if not self.is_authenticated:
            dlg = LoginDialog(self)
            if dlg.exec() == QDialog.Accepted:
                # This is where future API logic will go
                self.is_authenticated = True
                self.login_action.setText("Logout")
                self.statusBar().showMessage("Logged in to Lasagna Love", 5000)
        else:
            self.is_authenticated = False
            self.user_token = None
            self.login_action.setText("Login to Lasagna Love...")
            self.statusBar().showMessage("Logged out", 5000)

    def populate_templates(self):
        self.template_list.blockSignals(True)
        self.template_list.clear()
        
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        
        # Scan both Bundled (Resources) and User (Documents) folders
        names = set()
        if BUNDLED_TEMPLATES_DIR.exists():
            names.update(f.stem for f in BUNDLED_TEMPLATES_DIR.glob("*.txt"))
        if TEMPLATES_DIR.exists():
            names.update(f.stem for f in TEMPLATES_DIR.glob("*.txt"))

        for name in sorted(list(names)):
            self.template_list.addItem(name)
            
        self.template_list.blockSignals(False)
        if self.template_list.count() > 0:
            self.template_list.setCurrentRow(0)

    def check_banner(self):
        name_empty = not self.settings.get("user_name", "").strip()
        show_alert = self.settings.get("show_name_alert", True)
        self.banner_widget.setVisible(name_empty and show_alert)

    def hide_banner_permanently(self):
        if self.banner_dont_show.isChecked():
            self.settings["show_name_alert"] = False
            self.save_settings()
            self.banner_widget.setVisible(False)

    def open_documentation(self):
        QMessageBox.information(self, "Documentation", "App documentation is coming soon!")

    def open_website(self):
        QDesktopServices.openUrl(QUrl("https://lasagnalove.org"))

    def report_bug(self):
        QDesktopServices.openUrl(QUrl("https://docs.google.com/forms/d/e/1FAIpQLSf_2jp46e-S9P5Db97bmuMKrlmy7X8jLh2dArsNYtikwXphjQ/viewform?usp=publish-editor"))

    def show_about_dialog(self):
        QMessageBox.about(self, "About BatchDispatch", 
            f"<b>BatchDispatch v{parsing.VERSION}</b><br><br>"
            "A specialized tool for Lasagna Love volunteers to manage outreach and deliveries.<br>")

    def check_for_updates(self, manual=False):
        """Checks a remote URL for the latest version string."""
        update_url = "https://api.github.com/repos/jevans0525/LL-BatchDispatch/releases/latest"
        
        try:
            with urllib.request.urlopen(update_url, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get("tag_name", "1.0.0").lstrip('v')
                download_url = data.get("html_url", "https://lasagnalove.org")

                # Proper version comparison
                def v_tuple(v): return tuple(map(int, (re.sub(r'[^0-9.]', '', v).split('.'))))
                
                if v_tuple(latest_version) > v_tuple(parsing.VERSION):
                    self.update_detected.emit(latest_version, download_url)
                elif manual:
                    # Manual check needs to return to main thread too
                    QTimer.singleShot(0, lambda: QMessageBox.information(
                        self, "Up to Date", f"You are running the latest version (v{parsing.VERSION})."))
        except Exception as e:
            error_text = str(e)
            logging.error(f"Failed to check for updates: {error_text}")
            if manual:
                QTimer.singleShot(0, lambda: QMessageBox.warning(
                    self, "Update Check Failed", f"Could not reach the update server.\n\nError: {error_text}"))

    def show_update_dialog(self, version: str, url: str):
        """Displays the update prompt on the main thread."""
        reply = QMessageBox.question(
            self, "Update Available",
            f"A newer version ({version}) of BatchDispatch is available.\n\n"
            "Would you like to visit the download page now?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl(url))

    def toggle_dock(self, checked):
        self.dock.setVisible(checked)
        self.settings["show_docked_editor"] = checked
        self.save_settings()

    def load_dock_template(self):
        curr = self.template_list.currentItem()
        if not curr: return
        name = curr.text()
        
        # User templates in Documents override bundled templates in Resources
        user_path = TEMPLATES_DIR / f"{name}.txt"
        bundled_path = BUNDLED_TEMPLATES_DIR / f"{name}.txt"
        
        if user_path.exists():
            text = user_path.read_text(encoding="utf-8")
        elif bundled_path.exists():
            text = bundled_path.read_text(encoding="utf-8")
        else:
            text = ""
            
        self.dock_editor.blockSignals(True)
        self.dock_editor.setPlainText(text)
        self.dock_editor.blockSignals(False)
        self.undo_stack.clear()
        self._commit_undo_snapshot()

    def _save_current_dock_template(self):
        curr = self.template_list.currentItem()
        if not curr: return
        name = curr.text()
        
        text = self.dock_editor.toPlainText()
        path = TEMPLATES_DIR / f"{name}.txt"
        path.write_text(text, encoding="utf-8")

    def save_dock_template(self):
        self._save_current_dock_template()
        QMessageBox.information(self, "Saved", "Template saved successfully.")

    def open_import_dialog(self):
        dlg = ImportDialog(self, self.settings)
        if dlg.exec() == QDialog.Accepted and dlg.imported_df is not None:
            imported = dlg.imported_df.copy()
            if "Select" not in imported.columns:
                imported.insert(0, "Select", True)
            self.model.beginResetModel()
            if self.model._df.empty:
                self.model._df = imported
            else:
                self.model._df = pd.concat([self.model._df, imported], ignore_index=True)
            self.model.endResetModel()
            logging.info(f"Accepted {len(imported)} rows into the main tracking model.")
            self.statusBar().showMessage(f"Successfully imported {len(imported)} rows.", 5000)

    def clear_selected_rows(self):
        self.statusBar().clearMessage()
        if self.model._df.empty:
            return
            
        if "Select" not in self.model._df.columns:
            return
            
        selected_mask = self.model._df["Select"] == True
        selected_count = selected_mask.sum()
        
        if selected_count == 0:
            QMessageBox.information(self, "No Selection", "No rows are currently selected via the checkboxes.")
            return
            
        reply = QMessageBox.question(self, "Confirm Clear", f"Are you sure you want to remove the {selected_count} selected row(s)?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Save state for undo before modification
            self.row_undo_stack.append(self.model._df.copy())
            if len(self.row_undo_stack) > 10:
                self.row_undo_stack.pop(0)
            self.undo_delete_action.setEnabled(True)

            self.model.beginResetModel()
            self.model._df = self.model._df[~selected_mask].reset_index(drop=True)
            self.model.endResetModel()
            self.statusBar().showMessage(f"Removed {selected_count} rows.", 5000)

    def undo_clear_rows(self):
        if self.row_undo_stack:
            previous_df = self.row_undo_stack.pop()
            self.model.beginResetModel()
            self.model._df = previous_df
            self.model.endResetModel()
            self.undo_delete_action.setEnabled(len(self.row_undo_stack) > 0)
            self.statusBar().showMessage("Restored previously deleted rows.", 5000)

    def select_all_rows(self):
        if not self.model._df.empty and "Select" in self.model._df.columns:
            self.model.beginResetModel()
            self.model._df["Select"] = True
            self.model.endResetModel()

    def deselect_all_rows(self):
        if not self.model._df.empty and "Select" in self.model._df.columns:
            self.model.beginResetModel()
            self.model._df["Select"] = False
            self.model.endResetModel()

    def update_search(self, text):
        self.proxy_model.setFilterString(text)
        self.highlight_delegate.set_filter_text(text)
        self.table_view.viewport().update()

    def save_settings(self):
        logging.info("Saving application settings to disk.")
        CONFIG_PATH.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")

    def apply_dark_mode(self, enabled: bool):
        app = QApplication.instance()
        app.setStyle("Fusion")
        if enabled:
            p = app.palette()
            p.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            p.setColor(QPalette.ColorRole.WindowText, Qt.white)
            p.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
            p.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            p.setColor(QPalette.ColorRole.ToolTipBase, Qt.white)
            p.setColor(QPalette.ColorRole.ToolTipText, Qt.white)
            p.setColor(QPalette.ColorRole.Text, Qt.white)
            p.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            p.setColor(QPalette.ColorRole.ButtonText, Qt.white)
            p.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            p.setColor(QPalette.ColorRole.HighlightedText, Qt.black)
            app.setPalette(p)
        else:
            app.setPalette(QApplication.style().standardPalette())

    def open_settings(self):
        dlg = ConfigDialog(self, self.settings)
        dlg.outreachRequested.connect(self.edit_outreach_template)
        dlg.deliveryRequested.connect(self.edit_delivery_template)
        if dlg.exec() == QDialog.Accepted:
            self.settings = dlg.updated_settings()
            self.save_settings()
            self.apply_dark_mode(self.settings.get("dark_mode", True))
            self.model.settings = self.settings
            self.table_view.viewport().update()
            self.check_banner()
            QMessageBox.information(self, "Settings Saved", "Configuration updated.")

    def edit_outreach_template(self):
        path = TEMPLATES_DIR / "Outreach Template.txt"
        if not path.exists():
            res_path = BUNDLED_TEMPLATES_DIR / "Outreach Template.txt"
            initial_text = res_path.read_text(encoding="utf-8") if res_path.exists() else "Hi [First Name],\n\nWe have your delivery scheduled for [Scheduled]."
        else:
            initial_text = path.read_text(encoding="utf-8")

        placeholders = ["MyName"] + parsing.CANONICAL_DATA_HEADERS
        dlg = TemplateDialog(self, "Edit Outreach Template", initial_text, placeholders=placeholders)
        if dlg.exec() == QDialog.Accepted:
            path.write_text(dlg.get_text(), encoding="utf-8")

    def edit_delivery_template(self):
        path = TEMPLATES_DIR / "Delivery Template.txt"
        if not path.exists():
            res_path = BUNDLED_TEMPLATES_DIR / "Delivery Template.txt"
            initial_text = res_path.read_text(encoding="utf-8") if res_path.exists() else "Stop #[Deliverystoporder]\nName: [First Name] [Last Name]\nAddress: [Address 1]\nPhone: [Phone number]."
        else:
            initial_text = path.read_text(encoding="utf-8")

        placeholders = ["MyName"] + parsing.CANONICAL_DATA_HEADERS + ["Deliverystoporder", "fullname", "fulladdress", "contactphone", "allergyflag", "delivery_note"]
        dlg = TemplateDialog(self, "Edit Delivery Template", initial_text, placeholders=placeholders)
        if dlg.exec() == QDialog.Accepted:
            path.write_text(dlg.get_text(), encoding="utf-8")

    def show_column_menu(self, pos):
        menu = QMenu(self)
        for i in range(self.model.columnCount()):
            col_name = self.model.headerData(i, Qt.Horizontal)
            if not col_name:
                continue
            action = QAction(col_name, menu)
            action.setCheckable(True)
            action.setChecked(not self.table_view.isColumnHidden(i))
            action.setData(i)
            action.toggled.connect(self.toggle_column_visibility)
            menu.addAction(action)
        menu.exec(self.table_view.horizontalHeader().mapToGlobal(pos))
        
    def toggle_column_visibility(self, checked):
        action = self.sender()
        if action:
            col = action.data()
            self.table_view.setColumnHidden(col, not checked)

    def populate_tags(self):
        self.tag_list.clear()
        self.tag_list.addItem("[MyName]")
        for h in parsing.CANONICAL_DATA_HEADERS:
            self.tag_list.addItem(f"[{h}]")
        custom_tags = self.settings.get("custom_tags", {})
        for t in custom_tags:
            self.tag_list.addItem(f"[{t}]")

    def create_tag(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Create Tag")
        lay = QFormLayout(dlg)
        tag_name = QLineEdit()
        tag_field = QComboBox()
        tag_field.addItems(parsing.CANONICAL_DATA_HEADERS)
        lay.addRow("Tag Name (without brackets):", tag_name)
        lay.addRow("Information to use:", tag_field)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)
        if dlg.exec() == QDialog.Accepted:
            name = tag_name.text().strip("[] ")
            if name:
                if name in parsing.CANONICAL_DATA_HEADERS:
                    QMessageBox.warning(self, "Invalid Name", "Cannot use a canonical header name for a custom tag.")
                    return
                if "custom_tags" not in self.settings:
                    self.settings["custom_tags"] = {}
                self.settings["custom_tags"][name] = tag_field.currentText()
                self.save_settings()
                self.populate_tags()

    def insert_tag(self):
        curr = self.tag_list.currentItem()
        if curr:
            self.dock_editor.insertPlainText(curr.text())
            self.dock_editor.setFocus()

    def remove_tag(self):
        curr = self.tag_list.currentItem()
        if curr:
            tag_text = curr.text().strip("[]")
            if tag_text in parsing.CANONICAL_DATA_HEADERS or tag_text == "MyName":
                QMessageBox.warning(self, "Error", "Cannot remove canonical header tags.")
                return
            reply = QMessageBox.question(self, "Confirm Remove", f"Are you sure you want to remove tag [{tag_text}]?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                if "custom_tags" in self.settings and tag_text in self.settings["custom_tags"]:
                    del self.settings["custom_tags"][tag_text]
                    self.save_settings()
                    self.populate_tags()

    def import_template(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Template", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            src = Path(file_path)
            dest = TEMPLATES_DIR / src.name
            if dest.exists():
                reply = QMessageBox.question(self, "Overwrite", f"Template '{src.name}' already exists. Overwrite?", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            self.populate_templates()
            self.statusBar().showMessage(f"Imported template: {src.name}", 5000)

    def create_template(self):
        name, ok = QInputDialog.getText(self, "New Template", "Template Name:")
        if ok and name.strip():
            name = name.strip()
            path = TEMPLATES_DIR / f"{name}.txt"
            if path.exists():
                QMessageBox.warning(self, "Error", "Template name already exists.")
                return
            path.write_text("", encoding="utf-8")
            self.populate_templates()

    def remove_template(self):
        curr = self.template_list.currentItem()
        if not curr: return
        name = curr.text()
        reply = QMessageBox.question(self, "Confirm Remove", f"Are you sure you want to remove template '{name}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            path = TEMPLATES_DIR / f"{name}.txt"
            if path.exists():
                path.unlink()
            self.populate_templates()

    def _commit_undo_snapshot(self):
        text = self.dock_editor.toPlainText()
        if not self.undo_stack or self.undo_stack[-1][1] != text:
            self.undo_stack.append((dt.datetime.now().strftime("%H:%M:%S"), text))
            if len(self.undo_stack) > 20:
                self.undo_stack.pop(0)

    def show_undo_menu(self):
        menu = QMenu(self)
        for timestamp, text in reversed(self.undo_stack):
            snippet = text[:20].replace('\n', ' ') + "..."
            action = QAction(f"{timestamp} - {snippet}", menu)
            action.setData(text)
            action.triggered.connect(self.apply_undo_snapshot)
            menu.addAction(action)
        if not menu.isEmpty():
            menu.exec(QCursor.pos())

    def apply_undo_snapshot(self):
        action = self.sender()
        if action:
            text = action.data()
            self.dock_editor.blockSignals(True)
            self.dock_editor.setPlainText(text)
            self.dock_editor.blockSignals(False)

    def save_and_generate(self):
        self._save_current_dock_template()
        
        # Use checkboxes for generation selection
        if not self.model._df.empty and "Select" in self.model._df.columns:
            df_to_use = self.model._df[self.model._df["Select"] == True]
        else:
            df_to_use = self.model._df
            
        if df_to_use.empty:
            QMessageBox.warning(self, "No Selection", "Please select at least one row using the checkboxes to generate.")
            return
            
        reply = QMessageBox.question(self, "Generate", "Use current template and selected requesters to generate a message?", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
            
        curr = self.template_list.currentItem()
        if not curr: return
        name = curr.text()
        
        template_text = self.dock_editor.toPlainText()
        custom_tags = self.settings.get("custom_tags", {})
        
        if name == "Delivery Template":
            err = reports.validate_delivery_order_consecutive(df_to_use)
            if err:
                QMessageBox.warning(self, "Validation Error", err)
                return
            logging.info(f"Generating delivery report for {len(df_to_use)} items.")
            generated_text = reports.build_delivery_text(df_to_use, template_text, self.settings.get("user_name", "Volunteer"), custom_tags)
        else:
            logging.info(f"Generating outreach report for {len(df_to_use)} items.")
            generated_text = reports.build_outreach_text(df_to_use, template_text, self.settings.get("user_name", "Volunteer"), custom_tags)
            
        dlg = QDialog(self)
        dlg.setWindowTitle("Preview Generated Message")
        dlg.resize(600, 400)
        lay = QVBoxLayout(dlg)
        preview = QPlainTextEdit(generated_text)
        preview.setReadOnly(True)
        lay.addWidget(preview)
        
        btn_lay = QHBoxLayout()
        btn_print = QPushButton("Print")
        btn_save = QPushButton("Create .txt Document")
        btn_close = QPushButton("Close")
        btn_lay.addWidget(btn_print)
        btn_lay.addWidget(btn_save)
        btn_lay.addWidget(btn_close)
        lay.addLayout(btn_lay)
        
        btn_print.clicked.connect(lambda: self.print_text(generated_text))
        btn_save.clicked.connect(lambda: self.save_text_as_file(generated_text))
        btn_close.clicked.connect(dlg.accept)
        
        dlg.exec()

    def print_text(self, text):
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter
        from PySide6.QtGui import QTextDocument
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.Accepted:
            doc = QTextDocument()
            doc.setPlainText(text)
            doc.print_(printer)
            
    def save_text_as_file(self, text):
        initial_dir = self.settings.get("save_location", "")
        path, _ = QFileDialog.getSaveFileName(self, "Save Document", initial_dir, "Text Files (*.txt)")
        if path:
            Path(path).write_text(text, encoding="utf-8")

def load_settings() -> dict:
    defaults = {
        "user_name": "",
        "addr2_color": "#0d6efd",
        "allergy_color": "#ff4d4f",
        "date_format": "MM/DD/YYYY",
        "save_location": str(DOCS_DIR),
        "dark_mode": True,
        "show_welcome_screen": True,
        "highlight_allergy": True,
        "highlight_addr2": True,
        "show_name_alert": True,
        "show_docked_editor": False
    }
    if CONFIG_PATH.exists():
        try:
            loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            defaults.update(loaded)
            return defaults
        except Exception:
            return defaults
    return defaults

def ensure_initial_settings():
    """Initializes app directory and config."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    settings = load_settings()
    
    if not CONFIG_PATH.exists() or settings.get("show_welcome_screen", True):
        dlg = FirstRunDialog()
        res = dlg.exec()
        
        defaults = settings if CONFIG_PATH.exists() else load_settings()
        if res in (FirstRunDialog.ResultSettings, FirstRunDialog.ResultContinue):
            if hasattr(dlg, "dont_show_cb"):
                defaults["show_welcome_screen"] = not dlg.dont_show_cb.isChecked()
            if dlg.name_edit.text().strip():
                defaults["user_name"] = dlg.name_edit.text().strip()
            logging.info("Configuring settings from first-run wizard.")
            CONFIG_PATH.write_text(json.dumps(defaults, indent=2), encoding="utf-8")
            return 2 if res == FirstRunDialog.ResultSettings else 1
        logging.info("First-run wizard cancelled.")
        return False
    return 1

def main():
    setup_logging()
    sys.excepthook = handle_exception
    logging.info("--- Session Started ---")
    # 1. Initialize Application First
    app = QApplication(sys.argv)
    
    # 2. Check settings/First Run before showing Main Window
    init_res = ensure_initial_settings()
    if not init_res:
        sys.exit(0)
        
    settings = load_settings()
    
    # 3. Launch Main Window
    try:
        w = MainWindow(settings)
        w.show()
        if init_res == 2:
            w.open_settings()
        sys.exit(app.exec())
    except Exception as e:
        # Catch-all for remaining GUI initialization errors
        print(f"Critical Startup Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
