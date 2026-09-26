[Unit]
Description=Excellent-Nd runtime for %i
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
WorkingDirectory=%h
ExecStart=__PYTHON__ __RUNNER__ %i
Restart=always
RestartSec=10
TimeoutStopSec=10
KillMode=control-group

[Install]
WantedBy=default.target
