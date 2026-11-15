{#- Evidence states for Gold boolean rule flags (mirrors
    serving.marts.climate.climate_products._evidence_status). A Gold flag of
    false cannot distinguish "observed negative" from "missing measurement", so
    serving publishes positive / negative / inconclusive / not_evaluated and a
    tri-state flag that is null unless the evidence decides it. -#}
{% macro evidence_status(flag, negative, observed) -%}
case
    when coalesce({{ flag }}, false) then 'positive'
    when {{ negative }} then 'negative'
    when {{ observed }} then 'inconclusive'
    else 'not_evaluated'
end
{%- endmacro %}

{% macro decided_flag(status) -%}
case {{ status }} when 'positive' then true when 'negative' then false end
{%- endmacro %}
