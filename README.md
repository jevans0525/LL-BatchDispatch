# LL-BatchDispatch
BatchDispatch (v1.0.0)

Developed by James Evans for Lasagna Love, BatchDispatch is a professional-grade desktop suite designed to empower Lasagna Love volunteers. 

1. Installation & Setup

BatchDispatch is deployed via a professional installation wizard for a seamless "concierge" experience.

Run the Installer: Open BatchDispatch_Setup.exe.

Follow the Wizard: The app installs to your local user directory to ensure persistent access to your templates and settings without requiring administrator privileges for every run.

First-Time Welcome: On your first launch, you will see a Welcome Screen. Enter your first name—this is used to automatically fill the [MyName] tag in all your messages.

Configuration: Access the Settings menu (Ctrl+,) to set your default date formats and chosen highlight colors.

2. Advanced Logistics Features

We have built specific features to solve the unique "last mile" challenges of volunteer delivery.

🔒 Security, Trust, and Privacy
Because BatchDispatch is a custom, community-developed tool for Lasagna Love volunteers rather than a commercial product from a large corporation, you may encounter a security warning during installation.

🛡️ Why do I see a "Windows Protected Your PC" warning?
Windows uses a system called SmartScreen to verify software. Because this app is "unsigned" (which requires a costly annual corporate certificate), Windows flags it as being from an "Unknown Publisher".

To install, simply:

Click "More Info" on the blue warning box.

Click "Run anyway" to launch the installer.

🤝 Our Commitment to You and Our Neighbors
Local Data Only: BatchDispatch is built with a "Privacy First" architecture. Every piece of requester data you import stays on your hard drive in a local encrypted folder (~/.batch_dispatch_app). No neighbor information is ever uploaded to a cloud server or shared by this application.

No Hidden Trackers: There are no analytics, "phone-home" features, or hidden background processes. The app only connects to the internet if you explicitly click the "Visit Lasagna Love" link in the help menu.

Open Source & Transparent: This tool was created by a fellow volunteer at DragonWire Studios. The source code is available on GitHub for anyone in the community to audit, ensuring the highest standards of transparency and safety.

🛡️ Verified Safety
If you or your IT department have concerns, you are encouraged to scan the BatchDispatch_Setup.exe with any reputable antivirus software (such as Microsoft Defender or Malwarebytes) before installation. You will find that the application is clean and focused solely on making your volunteer work easier.


🏢 Address 2 / Apartment Highlighting

In high-density areas, missing an apartment number is the most common cause of delivery delay.

The Feature: BatchDispatch automatically scans the Address 2 column.

How it Works: Any text in the "Address 2" field is automatically highlighted in your chosen color (default: Vibrant Blue) within the main table.

The Benefit: This ensures you catch apartment numbers, building letters, and gate codes at a glance before you leave for your run.

⚠️ Dietary & Allergy Safety

To protect our neighbors, we have integrated a multi-tier safety system:

Visual Alerts: Any row flagged with a "YES" in a dietary or allergy column is automatically highlighted in Vibrant Red.

Smart Validation: If you attempt to generate a "Standard" outreach report for a flagged row, the app will pause and request explicit confirmation to ensure you are using the correct safety protocols.

🔍 Real-Time "Highlight" Search

Contextual Filtering: As you type in the Search bar (Ctrl+F), the roster filters instantly.

Visual Focus: Every match within the table is highlighted in Orange, allowing you to find specific phone numbers or street names without scanning line-by-line.

3. The New Tag & Template System

We have migrated to a robust square-bracket [Tag] system for maximum reliability and ease of use.

Using the Template Dock

Toggle Editor: Use the "Toggle Template Editor" button to reveal the message workspace.

Insert Tags: Click on any "Available Tag" (like [First Name] or [Scheduled]) to insert it at your cursor position.

Live Highlighting: The editor uses Orange Syntax Highlighting for tags, so you can easily see where your data will be injected.

Standard Tags List

[MyName] - Your name from Settings
[First Name] - Requester's first name
[Family Size] - Total headcount for the meal
[Scheduled] - Your planned delivery date
[Address 1] - The primary street address

🛠️ Custom Tag Logic

If you import data with non-standard columns, use the Create Tag button. You can map any unique spreadsheet header to a custom bracket name (e.g., mapping "GateCode" to [Entry]), making BatchDispatch adaptable to any regional roster format.

4. Operation & Efficiency

Robust Data Import

Ctrl+V Integration: Simply copy rows from the Lasagna Love portal and press Ctrl+V in the Import window. The app handles the parsing and mapping automatically.

Deduplication: BatchDispatch automatically checks for and removes duplicate IDs during the import process to prevent double-deliveries.

Managing the Roster

Selection Checks: Use the "Select" column to batch your work. Use Select All or Deselect All to clear your workspace.

Undo History: We have implemented a 10-step Undo History for row deletions and a 20-step Undo Menu for the Template Editor. If you make a mistake, your data is safe.

Saving & Projects

Session Persistence: Your data is automatically saved to last_session.json when the app closes.

Run Projects: You can save specific delivery days as .json project files, allowing you to archive past runs and reload them later for reference.

5. Technical Requirements

OS: Windows 10/11

Engine: PySide6 & Pandas

Storage: Locally hosted (no data leaves your computer)

Created with care by James Evans for the Lasagna Love Community.
