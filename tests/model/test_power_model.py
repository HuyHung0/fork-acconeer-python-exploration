# Copyright (c) Acconeer AB, 2023-2024
# All rights reserved

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from acconeer.exptool import a121
from acconeer.exptool.a121.algo import distance, presence
from acconeer.exptool.a121.algo.presence import _configs as presence_configs
from acconeer.exptool.a121.model import power


CURRENT_LIMITS_ROOT = Path("stash/python_libs/acconeer-analyses/acconeer/analyses/a121/resources")

if not CURRENT_LIMITS_ROOT.exists() and not os.environ.get("CI", False):
    pytest.skip("Could not find stash and not running in CI", allow_module_level=True)


with (CURRENT_LIMITS_ROOT / "sensor_current_limits.yaml").open("r") as f:
    SENSOR_CURRENT_LIMITS = yaml.safe_load(f)

with (CURRENT_LIMITS_ROOT / "module_current_limits.yaml").open("r") as f:
    MODULE_CURRENT_LIMITS = yaml.safe_load(f)

with (CURRENT_LIMITS_ROOT / "inter_sweep_idle_states_limits.yaml").open("r") as f:
    INTER_SWEEP_IDLE_STATES = yaml.safe_load(f)


def _assert_percent_off_message(actual: float, expected: float, absolute_tolerance: float) -> None:
    percent_off = actual / expected - 1

    if percent_off < 0:
        message = f"Model underestimated by {-percent_off:.2%}"
    else:
        message = f"Model overestimated by {percent_off:.2%}"

    assert actual == pytest.approx(expected, abs=absolute_tolerance), message


@pytest.mark.parametrize(
    ("limit_name", "limits_dict", "actual"),
    [
        (
            "Idle state, deep_sleep",
            SENSOR_CURRENT_LIMITS,
            power.frame_idle(
                a121.IdleState.DEEP_SLEEP, duration=1, module=power.Module.none()
            ).average_current,
        ),
        (
            "Idle state, sleep",
            SENSOR_CURRENT_LIMITS,
            power.frame_idle(
                a121.IdleState.SLEEP, duration=1, module=power.Module.none()
            ).average_current,
        ),
        (
            "Idle state, ready",
            SENSOR_CURRENT_LIMITS,
            power.frame_idle(
                a121.IdleState.READY, duration=1, module=power.Module.none()
            ).average_current,
        ),
        (
            "Measurement state, profile 1",
            SENSOR_CURRENT_LIMITS,
            power.subsweep_active(
                a121.SubsweepConfig(profile=a121.Profile.PROFILE_1),
                high_speed_mode=False,
                subsweep_index=0,
                module=power.Module.none(),
            ).average_current,
        ),
        (
            "Measurement state, profile 2",
            SENSOR_CURRENT_LIMITS,
            power.subsweep_active(
                a121.SubsweepConfig(profile=a121.Profile.PROFILE_2),
                high_speed_mode=False,
                subsweep_index=0,
                module=power.Module.none(),
            ).average_current,
        ),
        (
            "Measurement state, profile 3",
            SENSOR_CURRENT_LIMITS,
            power.subsweep_active(
                a121.SubsweepConfig(profile=a121.Profile.PROFILE_3),
                high_speed_mode=False,
                subsweep_index=0,
                module=power.Module.none(),
            ).average_current,
        ),
        (
            "Measurement state, profile 4",
            SENSOR_CURRENT_LIMITS,
            power.subsweep_active(
                a121.SubsweepConfig(profile=a121.Profile.PROFILE_4),
                high_speed_mode=False,
                subsweep_index=0,
                module=power.Module.none(),
            ).average_current,
        ),
        (
            "Measurement state, profile 5",
            SENSOR_CURRENT_LIMITS,
            power.subsweep_active(
                a121.SubsweepConfig(profile=a121.Profile.PROFILE_5),
                high_speed_mode=False,
                subsweep_index=0,
                module=power.Module.none(),
            ).average_current,
        ),
        (
            "Hibernation state",
            SENSOR_CURRENT_LIMITS,
            power.power_state(
                power.Sensor.IdleState.HIBERNATE, duration=1, module=power.Module.none()
            ).average_current,
        ),
        (
            "Off state, ENABLE low",
            SENSOR_CURRENT_LIMITS,
            power.power_state(
                power.Sensor.IdleState.OFF, duration=1, module=power.Module.none()
            ).average_current,
        ),
        (
            "deep_sleep",
            INTER_SWEEP_IDLE_STATES,
            power.sweep_idle(
                a121.SensorConfig(inter_sweep_idle_state=a121.IdleState.DEEP_SLEEP),
                duration=1,
                module=power.Module.none(),
            ).average_current,
        ),
        (
            "ready",
            INTER_SWEEP_IDLE_STATES,
            power.sweep_idle(
                a121.SensorConfig(inter_sweep_idle_state=a121.IdleState.READY),
                duration=1,
                module=power.Module.none(),
            ).average_current,
        ),
        (
            "sleep",
            INTER_SWEEP_IDLE_STATES,
            power.sweep_idle(
                a121.SensorConfig(inter_sweep_idle_state=a121.IdleState.SLEEP),
                duration=1,
                module=power.Module.none(),
            ).average_current,
        ),
    ],
)
def test_sensor_limits(
    limit_name: str, limits_dict: dict[str, dict[str, float]], actual: float
) -> None:
    unit_factor = 1e-3

    expected_current = limits_dict[limit_name]["target"] * unit_factor
    absolute_tolerance = limits_dict[limit_name]["abs_tol"] * unit_factor

    assert actual == pytest.approx(expected_current, abs=absolute_tolerance)


@pytest.mark.parametrize(
    ("limit_name", "lower_idle_state"),
    [
        ("Off state, ENABLE low", power.Sensor.IdleState.OFF),
        ("Hibernation state", power.Sensor.IdleState.HIBERNATE),
    ],
)
def test_lower_idle_state_limits(
    limit_name: str,
    lower_idle_state: power.Sensor.LowerIdleState,
) -> None:
    unit = MODULE_CURRENT_LIMITS[limit_name]["limits"]["xm125"]["unit"]
    unit_factor = {"mA": 1e-3, "μA": 1e-6}[unit]

    expected_current = MODULE_CURRENT_LIMITS[limit_name]["limits"]["xm125"]["target"] * unit_factor
    absolute_tolerance = (
        MODULE_CURRENT_LIMITS[limit_name]["limits"]["xm125"]["abs_tol"] * unit_factor
    )

    avg_current = power.power_state(lower_idle_state, duration=0.1).average_current
    assert avg_current == pytest.approx(expected_current, abs=absolute_tolerance)


@pytest.mark.parametrize(
    ("limit_name", "session_config", "lower_idle_state", "algorithm"),
    [
        (
            "Distance, Default",
            distance.Detector._detector_to_session_config_and_processor_specs(
                distance.DetectorConfig(update_rate=1.0, close_range_leakage_cancellation=True),
                sensor_ids=[1],
            )[0],
            power.Sensor.IdleState.OFF,
            power.algo.Distance(),
        ),
        (
            "Distance, Close",
            distance.Detector._detector_to_session_config_and_processor_specs(
                distance.DetectorConfig(
                    start_m=0.05,
                    end_m=0.10,
                    update_rate=1.0,
                    close_range_leakage_cancellation=False,
                ),
                sensor_ids=[1],
            )[0],
            power.Sensor.IdleState.OFF,
            power.algo.Distance(),
        ),
        (
            "Distance, Close and far",
            distance.Detector._detector_to_session_config_and_processor_specs(
                distance.DetectorConfig(
                    start_m=0.05,
                    end_m=3.0,
                    update_rate=1.0,
                    close_range_leakage_cancellation=False,
                ),
                sensor_ids=[1],
            )[0],
            power.Sensor.IdleState.OFF,
            power.algo.Distance(),
        ),
        (
            "Distance, Far",
            distance.Detector._detector_to_session_config_and_processor_specs(
                distance.DetectorConfig(
                    start_m=0.25,
                    end_m=3.0,
                    update_rate=1.0,
                ),
                sensor_ids=[1],
            )[0],
            power.Sensor.IdleState.OFF,
            power.algo.Distance(),
        ),
        (
            "Presence, Medium range (12Hz)",
            a121.SessionConfig(
                presence.Detector._get_sensor_config(presence_configs.get_medium_range_config()),
            ),
            power.Sensor.IdleState.HIBERNATE,
            power.algo.Presence(),
        ),
        (
            "Presence, Short range (10Hz)",
            a121.SessionConfig(
                presence.Detector._get_sensor_config(presence_configs.get_short_range_config()),
            ),
            power.Sensor.IdleState.HIBERNATE,
            power.algo.Presence(),
        ),
        (
            "Presence, Low Power Wakeup (1Hz)",
            a121.SessionConfig(
                presence.Detector._get_sensor_config(presence_configs.get_low_power_config()),
            ),
            power.Sensor.IdleState.HIBERNATE,
            power.algo.Presence(),
        ),
    ],
)
def test_module_limits(
    limit_name: str,
    session_config: a121.SessionConfig,
    lower_idle_state: power.Sensor.LowerIdleState,
    algorithm: power.algo.Algorithm,
) -> None:
    unit = MODULE_CURRENT_LIMITS[limit_name]["limits"]["xm125"]["unit"]
    unit_factor = {"mA": 1e-3, "μA": 1e-6}[unit]

    expected_current = MODULE_CURRENT_LIMITS[limit_name]["limits"]["xm125"]["target"] * unit_factor
    absolute_tolerance = (
        MODULE_CURRENT_LIMITS[limit_name]["limits"]["xm125"]["abs_tol"] * unit_factor
    )

    avg_current = power.converged_average_current(
        session_config,
        lower_idle_state,
        absolute_tolerance / 4,
        algorithm=algorithm,
    )
    _assert_percent_off_message(avg_current, expected_current, absolute_tolerance)
