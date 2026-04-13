## LL-BatchDispatch

**BatchDispatch (v.99) 
April 13, 2026**

Developed by James Evans for Lasagna Love, **BatchDispatch** is a simple app created to support Lasagna Love volunteers  with their requesters and remove barriers to efficient communication. The primary use case for this app is a volunteer matching with multiple requesters at a time.

From Lasagnalove.org:

> "Our mission is to feed families, spread kindness, and strengthen communities. Through our neighbor-to-neighbor movement, we connect volunteer lasagna chefs who want to help with individuals and families in need, providing home-cooked lasagnas made with love.  
> We focus on removing barriers to asking for help, ensuring dignity and support, and delivering kindness without judgment or qualifications. Whether someone is facing financial challenges, emotional overwhelm, medical issues, or any other hardship, Lasagna Love strives to provide relief, hope, and connection through the simple yet profound gesture of a warm meal."


## Installation & Setup

1. [Download the latest stable version here!](https://github.com/jevans0525/LL-BatchDispatch/releases/download/v0.99/BatchDispatch_Setup.exe)
 2. Run the Installer: Open BatchDispatch_Setup.exe.
 3. Follow the Wizard: The app installs to your local user directory to ensure persistent access to your templates and settings    without requiring administrator privileges for every run.
 4. First-Time Welcome: On your first launch, you will see a Welcome Screen. Enter your first name—this is used to automatically fill the [MyName] tag in all your messages.
 5. Configuration: Access the Settings menu (Ctrl+,) to set your default date formats and chosen highlight colors.
 6. **Data Import**
To import your requester data, simply highlight and copy your matched requester rows from the Lasagna Love portal,  then switch to the app and click on Import Data, then paste your data in the Import window. The app handles the parsing and mapping automatically; a preview will be shown so you can confirm the data was imported and matched to the correct columns as intended.




## **Advanced Logistics Features:**

**🏢 Address 2 / Apartment Highlighting:** Being aware of apartment and unit numbers can be important when planning a delivery or dropping off in person. By default, the app highlights any info in the Address 2 column for awareness. This setting can be changed in the Settings menu.
 
  **⚠️ Dietary & Allergy Awareness:** Because dietary restrictions and allergies must be carefully confirmed and tracked, any row flagged with a "YES" in a dietary or allergy column is automatically highlighted in Vibrant Red. This setting can be changed in the Settings menu.
  
**Smart Validation:** If you attempt to generate a "Standard" outreach report for a flagged row, the app will pause and request explicit confirmation to ensure you are using the correct safety protocols.
  
  **🔍 Real-Time "Highlight" Search:**  Results will populate as you type in the Search bar (Ctrl+F). Every match within the table is highlighted in Orange, allowing you to find specific phone numbers or street names without scanning line-by-line.
  

## The Template Editor System

A robust square-bracket [Tag] system has been implemented for maximum reliability and ease of use.
  
**Using the Template Dock**
  Toggle Editor: Use the "Toggle Template Editor" button to reveal the message workspace.
  Insert Tags: Click on any "Available Tag" (like [First Name] or [Scheduled]) to insert it at your cursor position.
  Live Highlighting: The editor uses Orange Syntax Highlighting for tags, so you can easily see where your data will be injected.
  
**Standard Tags List**
  
  [MyName] - Your name (defined in Welcome message and/or Settings)
  [First Name] - Requester's first name (matches to 'First Name' column)
  [Family Size] - Total headcount for the meal (matches to 'First Name' column)
 [Address 1] - The primary street address (matches to 'Address 1' column)
  [Address 2] - The secondary street address, usually reserved for Apartment, Unit, etc (matches to 'Address 2' column)
  
  **🛠️ Custom Tag Logic**
  
You can map any unique spreadsheet header to a custom bracket name (e.g., mapping "GateCode" to [Entry]), making BatchDispatch adaptable to any regional roster format. Note: importing data from sources other than Lasagnalove.org is not currently supported and may result in errors or instability.


  
**Managing the Roster**
Selection Checks: Use the "Select" column to batch your work. Use Select All or Deselect All to clear your workspace.
Undo History: We have implemented a 10-step Undo History for row deletions and a 20-step Undo Menu for the Template Editor. If you make a mistake, your data is safe.
  
  **Saving & Projects**
    **Session Persistence:** Your data is automatically saved to last_session.json when the app closes.
    **Completed Projects:** You can save specific delivery days as .json project files, allowing you to archive past runs and reload them later for reference.

**Technical Requirements**

  OS: Windows 10/11
  
  Engine: PySide6 & Pandas
  
  Storage: Locally hosted (no data leaves your computer)
  
**A note on Security, Trust, and Privacy:**
Because BatchDispatch is a custom, community-developed tool for Lasagna Love volunteers rather than a commercial product from a large corporation, you may encounter a security warning during installation. Digital signed security certificates are quite expensive and are out of the scope of this volunteer project.
  
**Why do I see a "Windows Protected Your PC" warning?**
Windows uses a system called SmartScreen to verify software. Because this app is "unsigned" (which requires a costly annual corporate certificate), Windows flags it as being from an "Unknown Publisher".
To install, simply:
Click "More Info" on the blue warning box.
Click "Run anyway" to launch the installer.
  
**🤝 Our Commitment to You and Our Neighbors**
  Local Data Only: BatchDispatch is built with a "Privacy First" architecture. Every piece of requester data you import stays on your hard drive in a local encrypted folder (~/.batch_dispatch_app). No neighbor information is ever uploaded to a cloud server or shared by this application.
  
**No Hidden Trackers:** There are no analytics, "phone-home" features, or hidden background processes. The only use of online features is the "Visit Lasagna Love" link in the help menu, which will launch your default browser and navigate to lasaganalove.org.
  
**Open Source & Transparent:** The source code is available on GitHub for anyone in the community to audit, ensuring the highest standards of transparency and safety.
  
**🛡️ Verified Safety**
  If you or your IT department have concerns, you are encouraged to scan the BatchDispatch_Setup.exe with any reputable antivirus software (such as Microsoft Defender or Malwarebytes) before installation. You will find that the application is clean and focused solely on making your volunteer work easier.


  Created with care by James Evans for the Lasagna Love Community.
