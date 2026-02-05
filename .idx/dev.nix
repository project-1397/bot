{ pkgs, ... }:

{
  # ===============================
  # SYSTEM PACKAGES
  # ===============================
  packages = with pkgs; [
    # Node.js (LTS)
    nodejs_20

    # Package managers
    npm
    yarn
    pnpm

    # Dev tools
    git
    gh
    openssh

    # Download tools
    curl
    wget
    aria2

    # Archive tools
    unzip
    zip
    p7zip
    gzip
    xz

    # Build tools
    gcc
    gnumake
    python3

    # Process & debug
    htop
    tmux
    screen
    tree
    jq

    # File watcher
    inotify-tools

    # Network
    nettools
    iputils
    dnsutils

    # Runtime helpers
    bash
    nano
    vim

    # Cloud / backup
    rclone
  ];

  # ===============================
  # ENVIRONMENT VARIABLES
  # ===============================
  env = {
    NODE_ENV = "development";
    NPM_CONFIG_LOGLEVEL = "warn";
  };

  # ===============================
  # IDX WORKSPACE SETTINGS
  # ===============================
  idx = {
    extensions = [
      "dbaeumer.vscode-eslint"
      "esbenp.prettier-vscode"
      "ms-vscode.vscode-node-azure-pack"
      "ms-azuretools.vscode-docker"
      "eamodio.gitlens"
    ];

    workspace = {
      onCreate = {
        install = ''
          echo "=== Installing global npm tools ==="
          npm install -g pm2 nodemon
        '';
      };

      onStart = {
        start = ''
          echo "=== Workspace ready ==="
          node -v
          npm -v
          pm2 -v || true
          rclone version || true
        '';
      };
    };
  };
}
