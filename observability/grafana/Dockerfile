FROM grafana/grafana:12.1.0
COPY provisioning /etc/grafana/provisioning
COPY dashboards /etc/grafana/dashboards
ENV GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH=/etc/grafana/dashboards/credora-services-overview.json
