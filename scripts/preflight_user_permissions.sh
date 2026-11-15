#!/bin/bash
# Ensure /opt/ComfyUI/user is writable by non-root user even after volume mounts
mkdir -p /opt/ComfyUI/user/default
chown -R user:ai-dock /opt/ComfyUI/user
chmod -R 775 /opt/ComfyUI/user

# Disable unused auxiliary ai-dock services to eliminate supervisor fatal restart loops
for svc in caddy jupyter serviceportal comfyui_api_wrapper cloudflared quicktunnel; do
    if [ -f "/etc/supervisor/supervisord/conf.d/${svc}.conf" ]; then
        sed -i 's/autostart=true/autostart=false/' "/etc/supervisor/supervisord/conf.d/${svc}.conf"
    fi
done
