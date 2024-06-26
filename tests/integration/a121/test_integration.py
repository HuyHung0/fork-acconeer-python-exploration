# Copyright (c) Acconeer AB, 2022-2024
# All rights reserved
from __future__ import annotations

import typing as t

import numpy as np
import pytest

from acconeer.exptool import a121
from acconeer.exptool.a121._core import utils


@pytest.fixture
def client_kwargs(worker_tcp_port: int, a121_exploration_server: None) -> dict[str, t.Any]:
    return dict(ip_address="localhost", tcp_port=worker_tcp_port)


def test_can_connect(client_kwargs):
    with a121.Client.open(**client_kwargs) as client:
        assert client.connected


class TestMockExplorationServerDataParsing:
    @pytest.fixture
    def expected_sweep(self):
        return np.array(
            [100 + 100j, 101 + 101j, 102 + 102j, 103 + 103j, 104 + 104j],
        )

    @pytest.mark.parametrize(
        "config",
        [
            a121.SessionConfig(a121.SensorConfig(num_points=5, start_point=100), extended=True),
            a121.SessionConfig(
                [
                    {1: a121.SensorConfig(num_points=5, start_point=100)},
                    {1: a121.SensorConfig(num_points=5, start_point=100)},
                ]
            ),
            a121.SessionConfig(
                [
                    {1: a121.SensorConfig(num_points=5, start_point=100)},
                    {1: a121.SensorConfig(num_points=5, start_point=100)},
                    {1: a121.SensorConfig(num_points=5, start_point=100)},
                    {1: a121.SensorConfig(num_points=5, start_point=100)},
                    {1: a121.SensorConfig(num_points=5, start_point=100)},
                ]
            ),
        ],
    )
    def test_sweep(self, config: a121.SessionConfig, expected_sweep, client_kwargs):
        assert config.extended
        with a121.Client.open(**client_kwargs) as client:
            client.setup_session(config)

            client.start_session()
            result = client.get_next()
            client.stop_session()

            assert isinstance(result, list)
            for _, _, value in utils.iterate_extended_structure(result):
                for sweep in value.frame:
                    np.testing.assert_equal(sweep, expected_sweep)


@pytest.mark.parametrize("prf", list(a121.PRF))
def test_setup_with_all_prfs(prf: a121.PRF, client_kwargs) -> None:
    with a121.Client.open(**client_kwargs) as client:
        client.setup_session(a121.SensorConfig(prf=prf, profile=a121.Profile.PROFILE_1))
