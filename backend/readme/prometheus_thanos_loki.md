# Definitions
__Metrics:__ Stream data defined in Prometheus format \
__Query:__ Payload from /query api \
__Block:__
  - Data is stored as blocks within Prometheus/Thanos
  - Initially stored in 2 hour blocks

__Compactor:__
  - A compactor will eventually compact the initial 2 hour blocks into longer blocks in the background.
  - Prometheus Compactor will create blocks larger blocks up to 10% of the retention, or 31 days, whichever is smaller. 

# Data Flow
__Sensor__ &rarr; __Gateway__ &rarr; __RabbitMQ__ &rarr; __Mqtt2tsdb__ &rarr; __Prometheus__ &rarr; __Thanos__ &rarr; __S3__

__Pods' logs__ &rarr; __Promtail__ &rarr; __Loki__ 

### Grafana sources
- __Thanos__
- __Loki__

# Prometheus
Stores metrics data in local TSDB for 24 hours.

# Thanos
Long term solution for Prometheus storage. Stores blocks in S3 bucket.

__Debugging:__
  - kubectl port-forward svc/thanos-bucketweb 8080 -n backend

# Loki
Converts logs into metrics. Config using a loki.yaml file.

__Labels:__
  - Applied to each stream. Used by Loki when querying
  - Can be dynamically defined.
    - Use regex to split a log line into capture groups. Then use 1 or more capture group as a label.