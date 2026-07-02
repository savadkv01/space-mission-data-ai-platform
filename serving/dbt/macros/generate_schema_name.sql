{#
    Use the custom `+schema:` value verbatim instead of dbt's default
    "<target_schema>_<custom_schema>" concatenation. The serving layer publishes
    stable, business-facing schema names (semantic / serving / serving_agg) that
    downstream consumers — the Superset `serving_duckdb` connection and the BI
    certified datasets — reference directly, so the `main_` prefix must not leak.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
