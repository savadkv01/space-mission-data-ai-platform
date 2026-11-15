-- Semantic: pollutant dimension (Phase 11b). Conformed dimension carrying
-- business-friendly names, units, AQI breakpoints, severity bands, and WHO thresholds for the
-- air-quality product. Static reference data single-sourced with
-- serving.marts.semantic.POLLUTANTS (there is no upstream Gold table).
select * from (
    values
        ('PM25', 'Fine Particulate Matter', 'surface_concentration', 'µg/m³', 'US_EPA', 15.0, 15.0,
         CAST('[{"aqi_low":0,"aqi_high":50,"value_low":0.0,"value_high":12.0,"label":"Good"},{"aqi_low":51,"aqi_high":100,"value_low":12.1,"value_high":35.4,"label":"Moderate"},{"aqi_low":101,"aqi_high":150,"value_low":35.5,"value_high":55.4,"label":"Unhealthy (sensitive)"},{"aqi_low":151,"aqi_high":200,"value_low":55.5,"value_high":150.4,"label":"Unhealthy"},{"aqi_low":201,"aqi_high":300,"value_low":150.5,"value_high":250.4,"label":"Very Unhealthy"},{"aqi_low":301,"aqi_high":500,"value_low":250.5,"value_high":500.4,"label":"Hazardous"}]' AS JSON),
         CAST('[]' AS JSON)),
        ('PM10', 'Coarse Particulate Matter', 'surface_concentration', 'µg/m³', 'US_EPA', 45.0, 45.0,
         CAST('[{"aqi_low":0,"aqi_high":50,"value_low":0.0,"value_high":54.0,"label":"Good"},{"aqi_low":51,"aqi_high":100,"value_low":55.0,"value_high":154.0,"label":"Moderate"},{"aqi_low":101,"aqi_high":150,"value_low":155.0,"value_high":254.0,"label":"Unhealthy (sensitive)"},{"aqi_low":151,"aqi_high":200,"value_low":255.0,"value_high":354.0,"label":"Unhealthy"},{"aqi_low":201,"aqi_high":300,"value_low":355.0,"value_high":424.0,"label":"Very Unhealthy"},{"aqi_low":301,"aqi_high":500,"value_low":425.0,"value_high":604.0,"label":"Hazardous"}]' AS JSON),
         CAST('[]' AS JSON)),
        ('NO2', 'Nitrogen Dioxide', 'column_density', 'mol/m²', 'n/a', CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST('[]' AS JSON), CAST('[]' AS JSON)),
        ('SO2', 'Sulphur Dioxide', 'column_density', 'mol/m²', 'n/a', CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST('[]' AS JSON), CAST('[]' AS JSON)),
        ('CO', 'Carbon Monoxide', 'column_density', 'mol/m²', 'n/a', CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST('[]' AS JSON), CAST('[]' AS JSON)),
        ('O3', 'Ozone', 'column_density', 'mol/m²', 'n/a', CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST('[]' AS JSON), CAST('[]' AS JSON)),
        ('CH4', 'Methane', 'column_density', 'ppb', 'n/a', CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST('[]' AS JSON), CAST('[]' AS JSON)),
        ('AOD', 'Aerosol Optical Depth', 'optical', 'unitless', 'n/a', CAST(NULL AS DOUBLE), 0.5,
         CAST('[]' AS JSON),
         CAST('[{"band":0,"label":"Clear","value_low":0.0,"value_high":0.2},{"band":1,"label":"Hazy","value_low":0.2,"value_high":0.5},{"band":2,"label":"Elevated","value_low":0.5,"value_high":1.0},{"band":3,"label":"High","value_low":1.0,"value_high":2.0},{"band":4,"label":"Very high","value_low":2.0,"value_high":5.0}]' AS JSON))
) as t(pollutant_code, pollutant_name, measure_type, canonical_unit, aqi_scheme, who_guideline, exceedance_threshold, aqi_breakpoints, severity_bands)
