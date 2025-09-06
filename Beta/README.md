# Fortnite Season 7 Emulator

A complete emulator for Fortnite Season 7 (Version 7.40) that allows you to run the game with a custom backend server, bypassing Epic Games' authentication and providing a local game environment.

## ⚠️ Important Legal Notice

This emulator is created for educational and preservation purposes only. You must have:
- Full permission from Epic Games to use this software
- A legitimate copy of Fortnite Season 7 (Version 7.40)
- Legal rights to modify and run the game files

The developers are not responsible for any misuse of this software.

## 🎮 Features

- **Complete Season 7 Experience**: Authentic Season 7 gameplay with all original features
- **Local Backend Server**: Custom server that handles all game API requests
- **Authentication Bypass**: Skip Epic Games login and update screens
- **GUI Launcher**: Easy-to-use interface for launching and managing the game
- **Request Redirection**: Automatic redirection of game requests to local backend
- **Profile Management**: Save and load player profiles and progress
- **Creative Mode Support**: Full Creative mode functionality
- **Matchmaking Simulation**: Basic matchmaking system for game modes

## 📋 Requirements

### System Requirements
- Windows 10/11 (64-bit)
- Python 3.8 or higher
- Administrator privileges (for hosts file modification)
- Fortnite Season 7 (Version 7.40) game files

### Python Dependencies
All dependencies are listed in `requirements.txt`:
- Flask (Web server framework)
- PyOpenSSL (SSL/TLS support)
- Cryptography (Certificate generation)
- PSUtil (Process management)
- PyYAML (Configuration management)
- PyWin32 (Windows-specific functionality)

## 🚀 Installation

### Step 1: Clone or Download
```bash
git clone <repository-url>
cd fortnite-season7-emulator
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure the Emulator
1. Edit `config.yaml` to match your setup
2. Ensure the server ports (8080, 8443) are available
3. Place your Fortnite 7.40 executable in an accessible location

### Step 4: Launch the Emulator
**The emulator now automatically requests administrator privileges!**

**Option 1: Double-click the batch file**
```
launch_emulator.bat
```

**Option 2: Use PowerShell launcher**
```
launch_admin.ps1
```

**Option 3: Run Python directly**
```bash
python main.py
```

All methods will automatically prompt for administrator privileges when needed.

## 🎯 Usage

### Starting the Emulator
1. **Easy Launch**: Double-click `launch_emulator.bat` or `launch_admin.ps1`
2. **UAC Prompt**: Click "Yes" when Windows asks for administrator privileges
3. **Automatic Setup**: Dependencies will be checked and installed if needed
4. **GUI Opens**: The launcher interface will appear automatically
5. **Backend Ready**: All services start automatically in the background

### Configuring Fortnite Path
1. Click "Browse" in the launcher
2. Select your Fortnite Season 7 executable (usually `FortniteClient-Win64-Shipping.exe`)
3. The path will be saved for future use

### Launch Arguments
The launcher comes with pre-configured launch arguments for Season 7:
- `-AUTH_LOGIN=unused` - Bypass login
- `-AUTH_PASSWORD=unused` - Bypass password
- `-AUTH_TYPE=epic` - Set auth type
- `-epicapp=Fortnite` - Set Epic app
- `-skippatchcheck` - Skip update checks
- `-nobe` - Disable BattlEye

You can modify these arguments in the launcher interface.

### Launching Fortnite
1. Ensure the backend server is running (status shows "Running")
2. Click "Launch Fortnite"
3. The game will start with custom backend redirection
4. Login screen and update checks will be bypassed

## 🔧 Configuration

### Main Configuration (`config.yaml`)
```yaml
server:
  host: "127.0.0.1"      # Backend server host
  port: 8080              # HTTP port
  ssl_port: 8443          # HTTPS port
  debug: true             # Enable debug mode

fortnite:
  version: "7.40"         # Game version
  season: 7               # Season number
  build_id: "4834769"     # Build identifier

launch_args:
  - "-AUTH_LOGIN=unused"
  - "-AUTH_PASSWORD=unused"
  # ... additional arguments
```

### SSL Certificates
The emulator automatically generates self-signed SSL certificates for HTTPS support. Certificates are stored in the `certs/` directory.

### Logging
Logs are stored in the `logs/` directory:
- `launcher_YYYYMMDD.log` - Launcher logs
- `backend_YYYYMMDD.log` - Backend server logs
- `redirector_YYYYMMDD.log` - Request redirection logs

## 🌐 Backend API

The backend server provides the following endpoints:

### Authentication
- `POST /account/api/oauth/token` - OAuth token generation
- `GET /account/api/oauth/verify` - Token verification
- `GET /account/api/public/account/{id}` - Account information

### Game Services
- `POST /fortnite/api/game/v2/profile/{accountId}/client/{command}` - Profile commands
- `GET /fortnite/api/matchmaking/session/findPlayer/{playerId}` - Matchmaking
- `GET /fortnite/api/calendar/v1/timeline` - Game timeline

### Content
- `GET /content/api/pages/fortnite-game` - Game content pages
- `GET /fortnite/api/storefront/v2/catalog` - Item shop catalog

## 🔒 Security Features

### Request Redirection
The emulator uses two methods to redirect Fortnite's requests:

1. **Hosts File Modification**: Redirects Epic Games domains to localhost
2. **HTTPS Proxy**: Advanced request interception and redirection

### Domain Redirection
The following Epic Games domains are redirected:
- `account-public-service-prod03.ol.epicgames.com`
- `fortnite-public-service-prod11.ol.epicgames.com`
- `lightswitch-public-service-prod06.ol.epicgames.com`
- And more...

## 🛠️ Troubleshooting

### Common Issues

**"Permission Denied" Error**
- Solution: Run as Administrator
- The emulator needs admin rights to modify the hosts file

**"Fortnite Failed to Launch"**
- Check that the Fortnite executable path is correct
- Ensure you have Fortnite Season 7 (Version 7.40)
- Verify launch arguments are appropriate for your setup

**"Backend Server Not Starting"**
- Check that ports 8080 and 8443 are not in use
- Verify Python dependencies are installed
- Check firewall settings

**"SSL Certificate Errors"**
- Delete the `certs/` folder and restart the emulator
- New certificates will be generated automatically

### Debug Mode
Enable debug mode in `config.yaml` for detailed logging:
```yaml
server:
  debug: true

logging:
  level: "DEBUG"
```

## 📁 Project Structure

```
fortnite-season7-emulator/
├── main.py                 # Main entry point
├── config.yaml            # Configuration file
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── launcher/             # GUI launcher
│   ├── __init__.py
│   └── main.py          # Launcher interface
├── backend/              # Backend server
│   ├── __init__.py
│   ├── server.py        # Main server
│   ├── auth_handler.py  # Authentication
│   ├── game_handler.py  # Game logic
│   └── content_handler.py # Content management
├── utils/                # Utility modules
│   ├── __init__.py
│   ├── config_manager.py # Configuration
│   ├── process_manager.py # Process handling
│   ├── logger.py        # Logging utilities
│   └── request_redirector.py # Request redirection
├── certs/                # SSL certificates (auto-generated)
└── logs/                 # Log files
```

## 🤝 Contributing

Contributions are welcome! Please ensure:
1. All code follows the existing style and structure
2. New features include appropriate documentation
3. Changes are tested thoroughly
4. Legal compliance is maintained

## 📄 License

This project is for educational and preservation purposes only. Users must comply with all applicable laws and Epic Games' terms of service.

## 🙏 Acknowledgments

- Epic Games for creating Fortnite
- The Fortnite community for preservation efforts
- Contributors to reverse engineering documentation

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs in the `logs/` directory
3. Ensure you're running as Administrator
4. Verify your Fortnite version is 7.40

---

**Remember**: This emulator is for educational purposes only. Always respect intellectual property rights and applicable laws.