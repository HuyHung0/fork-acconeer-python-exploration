# type: ignore

import json

import pytest

from acconeer.exptool import a121


@pytest.mark.xfail(reason="Not yet implemented")
def test_sweeps_per_frame():
    # Default value

    config = a121.SensorConfig()
    assert config.sweeps_per_frame == 1

    # Conversion

    config.sweeps_per_frame = 2
    assert config.sweeps_per_frame == 2
    assert isinstance(config.sweeps_per_frame, int)

    config.sweeps_per_frame = 3.0
    assert config.sweeps_per_frame == 3
    assert isinstance(config.sweeps_per_frame, int)

    with pytest.raises(TypeError):
        config.sweeps_per_frame = "not-an-int"

    with pytest.raises(TypeError):
        config.sweeps_per_frame = "3"

    with pytest.raises(TypeError):
        config.sweeps_per_frame = 3.5

    config = a121.SensorConfig(sweeps_per_frame=2)
    assert config.sweeps_per_frame == 2
    assert isinstance(config.sweeps_per_frame, int)

    config = a121.SensorConfig(sweeps_per_frame=3.0)
    assert config.sweeps_per_frame == 3
    assert isinstance(config.sweeps_per_frame, int)

    with pytest.raises(TypeError):
        a121.SensorConfig(sweeps_per_frame="not-an-int")

    with pytest.raises(TypeError):
        a121.SensorConfig(sweeps_per_frame="3")

    with pytest.raises(TypeError):
        a121.SensorConfig(sweeps_per_frame=3.5)

    # Validation

    config = a121.SensorConfig()

    with pytest.raises(ValueError):
        config.sweeps_per_frame = 0

    assert config.sweeps_per_frame == 1

    with pytest.raises(ValueError):
        a121.SensorConfig(sweeps_per_frame=0)

    # Documentation

    assert a121.SensorConfig.sweeps_per_frame.__doc__


def test_subsweep_properties_read_only():
    sensor_config = a121.SensorConfig()

    with pytest.raises(AttributeError):
        sensor_config.num_subsweeps = 1

    with pytest.raises(AttributeError):
        sensor_config.subsweeps = [a121.SubsweepConfig()]


@pytest.mark.xfail(reason="Not yet implemented")
def test_implicit_subsweep():
    sensor_config = a121.SensorConfig()

    assert sensor_config.num_subsweeps == 1
    assert len(sensor_config.subsweeps) == 1


@pytest.mark.xfail(reason="Not yet implemented")
def test_explicit_subsweeps():
    # Should be able to explicitly give the subsweeps

    sensor_config = a121.SensorConfig(
        subsweeps=[
            a121.SubsweepConfig(),
            a121.SubsweepConfig(),
        ],
    )

    assert sensor_config.num_subsweeps == 2
    assert len(sensor_config.subsweeps) == 2

    # Should be able to explicitly give the number of subsweeps

    sensor_config = a121.SensorConfig(
        num_subsweeps=2,
    )

    assert sensor_config.num_subsweeps == 2
    assert len(sensor_config.subsweeps) == 2

    # Giving both subsweeps and number of subsweeps should raise a ValueError

    with pytest.raises(ValueError):
        sensor_config = a121.SensorConfig(
            subsweeps=[
                a121.SubsweepConfig(),
                a121.SubsweepConfig(),
            ],
            num_subsweeps=2,
        )


@pytest.mark.xfail(reason="Not yet implemented")
def test_single_subsweep_param():
    # Make sure we don't happen to use the default value in the test
    assert a121.SubsweepConfig().hwaas not in [3, 4]

    sensor_config = a121.SensorConfig()

    # The sensor config and the (only) subsweep config should match
    assert sensor_config.hwaas == sensor_config.subsweeps[0].hwaas

    # We should be able to set values through the sensor config
    sensor_config.hwaas = 3
    assert sensor_config.hwaas == sensor_config.subsweeps[0].hwaas == 3

    # And the subsweep config
    sensor_config.subsweeps[0].hwaas = 4
    assert sensor_config.hwaas == sensor_config.subsweeps[0].hwaas == 4


@pytest.mark.xfail(reason="Not yet implemented")
def test_multiple_subsweeps_param():
    # Make sure we don't happen to use the default value in the test
    assert a121.SubsweepConfig().hwaas != 4

    sensor_config = a121.SensorConfig(num_subsweeps=2)

    # With multiple subsweeps, we should not be able to get/set subsweep parameters through the
    # sensor config

    with pytest.raises(Exception):
        _ = sensor_config.hwaas

    with pytest.raises(Exception):
        sensor_config.hwaas = 1

    # Make sure we can set subsweep parameters individually
    sensor_config.subsweeps[0].hwaas = 4
    assert sensor_config.subsweeps[1].hwaas != 4


@pytest.mark.xfail(reason="Not yet implemented")
def test_single_subsweep_at_instantiation():
    # Make sure we don't happen to use the default value in the test
    assert a121.SubsweepConfig().hwaas != 4

    sensor_config = a121.SensorConfig(
        subsweeps=[a121.SubsweepConfig(hwaas=4)],
    )

    # Make sure the subsweep is properly used

    assert sensor_config.hwaas == sensor_config.subsweeps[0].hwaas == 4


@pytest.mark.xfail(reason="Not yet implemented")
def test_eq():
    assert a121.SensorConfig() == a121.SensorConfig()
    assert a121.SensorConfig() != a121.SensorConfig(sweeps_per_frame=3)
    assert a121.SensorConfig() != a121.SensorConfig(num_subsweeps=2)
    assert a121.SensorConfig(num_subsweeps=2) == a121.SensorConfig(num_subsweeps=2)

    other = a121.SensorConfig(num_subsweeps=2)
    other.subsweeps[1].hwaas = 3
    assert a121.SensorConfig(num_subsweeps=2) != other


@pytest.mark.xfail(reason="Not yet implemented")
def test_from_to_dict():
    original_config = a121.SensorConfig(sweeps_per_frame=3)
    dict_ = original_config.to_dict()
    recreated_config = a121.SensorConfig.from_dict(dict_)
    assert recreated_config == original_config


@pytest.mark.xfail(reason="Not yet implemented")
def test_from_to_json():
    original_config = a121.SensorConfig(sweeps_per_frame=3)
    json_str = original_config.to_json()
    recreated_config = a121.SensorConfig.from_json(json_str)
    assert recreated_config == original_config

    dict_from_json = json.loads(json_str)
    dict_from_config = original_config.to_dict()
    assert dict_from_json == dict_from_config
