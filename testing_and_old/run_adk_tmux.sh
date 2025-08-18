#!/bin/bash

SESSION="adk_session"
CONDA_ENV_NAME="googleADK-env"
CLOUDFLARE_CONFIG="/home/joshua/.cloudflared/config.yml"

tmux new-session -d -s $SESSION
tmux send-keys -t $SESSION "bash -i -c 'conda activate $CONDA_ENV_NAME && adk web --host 0.0.0.0 --port 8000'" C-m
tmux split-window -h -t $SESSION
tmux send-keys -t $SESSION "bash -i -c 'conda activate $CONDA_ENV_NAME && cloudflared tunnel --config $CLOUDFLARE_CONFIG run my-adk-agent'" C-m