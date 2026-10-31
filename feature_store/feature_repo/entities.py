from feast import Entity
from feast.value_type import ValueType

satellite = Entity(
    name="satellite",
    value_type=ValueType.STRING,
    join_keys=["sat_key"],
    description="Satellite identity; simulated records remain explicitly labeled.",
)
mission = Entity(
    name="mission",
    value_type=ValueType.STRING,
    join_keys=["mission_key"],
    description="Mission identity; registration does not imply populated source data.",
)
launch_provider = Entity(
    name="launch_provider",
    value_type=ValueType.STRING,
    join_keys=["provider_key"],
    description="Launch provider identity.",
)
weather_scope = Entity(
    name="weather_scope",
    value_type=ValueType.STRING,
    join_keys=["weather_scope_key"],
    description="Geographic or mission scope for a weather observation.",
)
aoi = Entity(
    name="aoi",
    value_type=ValueType.STRING,
    join_keys=["aoi_key"],
    description="Area-of-interest key used by Earth-observation products.",
)
scene = Entity(
    name="scene",
    value_type=ValueType.STRING,
    join_keys=["scene_key"],
    description="Searchable image-scene metadata record, not image pixels.",
)
vessel = Entity(
    name="vessel",
    value_type=ValueType.STRING,
    join_keys=["vessel_key"],
    description="Vessel identity; activity remains blocked pending event-grain evidence.",
)

ENTITIES = [satellite, mission, launch_provider, weather_scope, aoi, scene, vessel]
