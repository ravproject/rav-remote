# Remote Laptop Control

This project allows you to control a laptop remotely using a mobile messaging app like Telegram or WhatsApp.

## Features

Currently, the project boasts **9 Core Features** divided into four logical categories:

**1. System Control & Monitoring**
- 📸 **Screenshot (`!screenshot`):** Capture the current laptop screen instantly.
- 📹 **Live Video (`!video`):** Record a short (5-15s) video clip of the screen activity.
- 💻 **System Info (`!sysinfo`):** View real-time CPU, RAM, and Disk usage.
- 🔋 **Smart Battery Alerts:** (Background) Automatically notifies you if the battery drops below 20% or the charger is unplugged.

**2. File & Media Management**
- 📂 **List Files (`!ls <path>`):** Browse files in allowed safe directories.
- ⬇️ **Download File (`!get <filename>`):** Send a file from the laptop to your phone.
- ⬆️ **Upload File:** Simply send a document or photo in the chat, and it will be saved to `~/Downloads/rav-remote`.

**3. Advanced Execution & Security**
- 🧠 **AI Voice & Text Commands:** Use natural language (or Voice Notes!) to command the bot (e.g., "Tolong ambil screenshot"). Powered by NVIDIA NIM and Google Speech-to-Text.
- 🛡️ **Intrusion Capture (`!webcam`):** Take a silent snapshot using the laptop's built-in webcam.
- 🔒 **Remote Lock (`!lock`):** Instantly lock the laptop screen (Windows/Mac/Linux).
- 🔄 **Remote Reboot (`!reboot`):** Restart the machine safely.

**4. Ultimate Power (Pro Features)**
- 🚀 **Sandbox Scripts (`!run <script>`):** Execute custom Python/Bash scripts isolated within Firejail/Docker.
- ⌨️ **Persistent Terminal (`!term`):** Open a fully interactive, background PTY shell. Perfect for running long commands or interacting with CLI agents like `opencode` or `git`.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- FFmpeg (Required for Video and Voice Note processing)
- Docker (Optional, for sandboxing)
- A Telegram Bot Token and User ID
- An NVIDIA NIM API Key (optional, for AI text processing)

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/remote-laptop-control.git
    cd remote-laptop-control
    ```

2.  **Install Node.js dependencies:**

    ```bash
    npm install
    ```

3.  **Run the automated setup:**

    ```bash
    npm run setup
    ```

    This command will automatically:
    - Create a Python virtual environment (`venv`).
    - Install all Python dependencies.
    - Generate secure secrets (OTP, JWT, API Keys).
    - Guide you through configuring your Telegram Bot Token and User ID.
    - Create your `.env` configuration file.

### Running the Application

You can run the application using Docker (recommended) or directly on your machine.

#### Docker (Recommended)

1.  **Build the Docker images:**

    ```bash
    docker-compose -f docker/docker-compose.yml build
    ```

2.  **Run the application:**

    ```bash
    docker-compose -f docker/docker-compose.yml up -d
    ```

#### Local Machine

Simply run one command to start the entire application (Agent and Telegram Bot):

```bash
npm start
```

Alternatively, you can run:
```bash
node run.js
```

To also run the WhatsApp bot (optional), run:
```bash
npm run whatsapp
# or
node run.js --whatsapp
```

## Configuration

The application is configured using environment variables. See the `.env.example` file for a list of all available options.

### Security

-   **OTP Secret:** Generate a new OTP secret and add it to your `.env` file. You will also need to add this secret to your authenticator app.
-   **JWT Secret:** Generate a new JWT secret and add it to your `.env` file.
-   **Allowed User IDs:** Add your Telegram and/or WhatsApp user IDs to the `ALLOWED_USER_IDS` environment variable.
-   **Agent API Key:** Generate a new API key for the agent and add it to your `.env` file.

### NVIDIA NIM

To use the AI-powered commands, you will need to sign up for an NVIDIA NIM account and generate an API key. Add the API key to your `.env` file.

## Usage

Once the application is running, you can send commands to your laptop from your mobile device.

### Telegram

1.  Start a chat with your Telegram bot.
2.  Send the `/start` command to authenticate.
3.  Enter the OTP from your authenticator app.
4.  You can now send commands to your laptop.

### WhatsApp

1.  Send a message to your WhatsApp number.
2.  You will be prompted to authenticate with an OTP.
3.  Enter the OTP from your authenticator app.
4.  You can now send commands to your laptop.

### Commands

See the `allowed_commands.yaml` file for a list of all available commands. 

**Terminal Mode:**
1. Type `!term` to enter the interactive shell.
2. Type any shell command (e.g., `ls`, `cd`, `python3`).
3. Type `!exit` to close the terminal session.

## Security Considerations

This application gives you full control over your laptop. It is important to understand the security implications before using it.

-   **Do not share your API keys or tokens with anyone.**
-   **Only use this application on devices and networks that you own and trust.**
-   **Review the `allowed_commands.yaml` file to ensure that you are comfortable with the commands that can be executed.**
-   **Keep your system and dependencies up to date.**

## Disclaimer

The developers of this project are not responsible for any damage or loss of data that may occur as a result of using this application. Use at your own risk.

## Contributing & Development

We enforce strict rules for adding new features to ensure the security and stability of the host machines. If you are developing new features or acting as an AI assistant modifying this codebase, you **MUST** read and adhere to the [DEVELOPMENT_STANDARDS.md](DEVELOPMENT_STANDARDS.md).
