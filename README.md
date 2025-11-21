# Offline Password Manager
A local password manager that lets you securely store and retrieve your account passwords. Each password is encrypted with a master key before being saved in a local SQLite database, so it is protected even if someone accesses your files. The program can generate strong random passwords for new accounts, and you can add or get credentials through a simple local API. Everything runs on your computer without needing an internet connection. 

# How to run
## To run the latest release
1. Go to the 'Releases' page to the right
2. Select the release compatible with your Operating System

### For Mac:
The project must be built from source using the instruction below.


## To run from the source code
- Download the latest binary from the Release section on the right on GitHub.  
- On the command line start virtual environment:
```
 python3 -m venv venv  
```
- On the command line activate venv.
```
source venv/bin/activate
```

Install requirements:
```
pip install -r requirements.txt

```
Run code:
```
python3 main.py
```

# How to contribute
Follow this project board to know the latest status of the project: [https://github.com/orgs/cis3296f25/projects/71]  

### How to build
- Use this github repository: ... 
- Specify what branch to use for a more stable release or for cutting edge development.  
- Use InteliJ 11
- Specify additional library to download if needed 
- What file and target to compile and run. 
- What is expected to happen when the app start.

# Component Diagram
```mermaid
graph TB
    subgraph "Entry Point"
        MAIN[main.py<br/>Start server & GUI]
    end

    subgraph "GUI Layer"
        LOGIN[LoginDialog]
        MAINWIN[MainWindow]
        DIALOGS[Add/Edit Dialogs]
        LIST[ListCredentialsWidget]
        SETTINGS[SettingsDialog]
    end

    subgraph "API Layer"
        API[Flask REST API]
        ROUTES[routes.py]
        CALLER[apiCallerMethods]
    end

    subgraph "Core"
        PM[passwordManager<br/>Vault ops]
        CRYPTO[Encryption<br/>KDF, VMK]
        VALIDATE[Password Strength]
    end

    subgraph "Storage"
        DB[(vault.db)]
        CONFIG[config.json]
    end

    subgraph "Resources"
        RES[Colors, Strings, Images]
    end

    MAIN --> API
    MAIN --> LOGIN
    LOGIN --> MAINWIN
    MAINWIN --> DIALOGS
    MAINWIN --> LIST
    MAINWIN --> SETTINGS

    MAINWIN --> CALLER
    DIALOGS --> CALLER
    LIST --> CALLER
    CALLER --> API
    API --> ROUTES
    ROUTES --> PM
    ROUTES --> VALIDATE
    PM --> CRYPTO
    PM --> DB

    SETTINGS --> CONFIG
    MAINWIN --> RES
    LOGIN --> RES
    SETTINGS --> RES

    classDef entry fill:#8ACE00,stroke:#6DA400,color:#000
    classDef gui fill:#5a9fff,stroke:#4a5f8f,color:#fff
    classDef api fill:#ff6b6b,stroke:#ee5a5a,color:#fff
    classDef core fill:#9f5aff,stroke:#8a4fdf,color:#fff
    classDef storage fill:#1e1e2f,stroke:#31314d,color:#fff
    classDef res fill:#F4F3F2,stroke:#e0e0e0,color:#000

    class MAIN entry
    class LOGIN,MAINWIN,DIALOGS,LIST,SETTINGS gui
    class API,ROUTES,CALLER api
    class PM,CRYPTO,VALIDATE core
    class DB,CONFIG storage
    class RES res

```

This diagram shows how the password manager is built. The GUI (blue boxes) is what users see - login screen, main window, dialogs for adding/editing passwords. When you do something in the GUI, it sends HTTP requests through the API layer (red boxes) to the core logic (purple boxes), which handles encryption and saves everything to the database. Even though it's a desktop app, we use a REST API internally so the GUI doesn't have to know about encryption or databases - it just makes requests and gets responses back. The whole thing starts from main.py which fires up both the web server and the GUI.
