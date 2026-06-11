# Remote Laptop Control

This project allows you to control a laptop remotely using a mobile messaging app like Telegram or WhatsApp.

## Features

- **Remote Command Execution:** Execute a predefined set of safe commands on your laptop from anywhere.
- **AI-Powered Commands:** Use natural language to execute commands (e.g., "take a screenshot").
- **Secure:** The system uses a multi-layered security approach, including OTP authentication, JWTs, and command sanitization.
- **Extensible:** The project is designed to be extensible, allowing you to add new commands and features easily.
- **Dockerized:** The project is fully dockerized, making it easy to deploy and run.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker
- A Telegram Bot Token and User ID
- A WhatsApp account (optional)
- An NVIDIA NIM API Key (optional)

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

## Security Considerations

This application gives you full control over your laptop. It is important to understand the security implications before using it.

-   **Do not share your API keys or tokens with anyone.**
-   **Only use this application on devices and networks that you own and trust.**
-   **Review the `allowed_commands.yaml` file to ensure that you are comfortable with the commands that can be executed.**
-   **Keep your system and dependencies up to date.**

## Disclaimer

The developers of this project are not responsible for any damage or loss of data that may occur as a result of using this application. Use at your own risk.
