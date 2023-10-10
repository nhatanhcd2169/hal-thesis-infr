FROM fluent/fluentd:edge

USER root
RUN gem install elasticsearch -v 8.8.0
RUN gem install fluent-plugin-elasticsearch
USER fluent