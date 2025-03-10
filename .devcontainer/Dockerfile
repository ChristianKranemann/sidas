FROM mcr.microsoft.com/vscode/devcontainers/python:3.13

# Install system dependencies
RUN apt-get update
RUN apt-get install -y 

# Create volume directory with correct permissions
RUN mkdir -p /workspaces/sida/.venv 
RUN chown vscode:vscode /workspaces/sida/.venv

# switch to vscode user
USER vscode
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

