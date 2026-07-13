-- Semantic: pollutant dimension (Phase 11b). Conformed dimension carrying
-- business-friendly names, units, AQI scheme and WHO thresholds for the
-- air-quality product. Static reference data single-sourced with
-- serving.marts.semantic.POLLUTANTS (there is no upstream Gold table).
select * from (
    values
        ('PM25', 'Fine Particulate Matter',   'surface_concentration', 'µg/m³',    'US_EPA', 15.0, 15.0),
        ('PM10', 'Coarse Particulate Matter', 'surface_concentration', 'µg/m³',    'US_EPA', 45.0, 45.0),
        ('NO2',  'Nitrogen Dioxide',          'column_density',        'mol/m²',   'n/a',    cast(null as double), cast(null as double)),
        ('SO2',  'Sulphur Dioxide',           'column_density',        'mol/m²',   'n/a',    cast(null as double), cast(null as double)),
        ('CO',   'Carbon Monoxide',           'column_density',        'mol/m²',   'n/a',    cast(null as double), cast(null as double)),
        ('O3',   'Ozone',                     'column_density',        'mol/m²',   'n/a',    cast(null as double), cast(null as double)),
        ('CH4',  'Methane',                   'column_density',        'ppb',      'n/a',    cast(null as double), cast(null as double)),
        ('AOD',  'Aerosol Optical Depth',     'optical',               'unitless', 'n/a',    cast(null as double), 0.5)
) as t(pollutant_code, pollutant_name, measure_type, canonical_unit, aqi_scheme, who_guideline, exceedance_threshold)
