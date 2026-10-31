{% macro register_gold_sources() %}
  {% if execute %}
    {% for node in graph.nodes.values() %}
      {% if node.resource_type == 'source' and node.source_name == 'gold' %}
        {% set location_template = node.meta.get('external_location') %}
        {% if location_template %}
          {% set location = location_template | replace('{name}', node.name) %}
          {% set file_query %}
            select count(*) as file_count from glob('{{ location }}')
          {% endset %}
          {% set file_result = run_query(file_query) %}
          {% if file_result and file_result.rows[0][0] > 0 %}
            {% do run_query(
              'create schema if not exists ' ~ adapter.quote(node.schema)
            ) %}
            {% set view_query %}
              create or replace view {{ adapter.quote(node.schema) }}.{{ adapter.quote(node.name) }}
              as select * from read_parquet('{{ location }}', union_by_name = true)
            {% endset %}
            {% do run_query(view_query) %}
          {% endif %}
        {% endif %}
      {% endif %}
    {% endfor %}
  {% endif %}
{% endmacro %}
