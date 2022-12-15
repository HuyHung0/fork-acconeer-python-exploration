# Copyright (c) Acconeer AB, 2022-2023
# All rights reserved

from __future__ import annotations

import json
from typing import Any, Optional, Union

import attrs

from acconeer.exptool.a121._core.utils import pretty_dict_line_strs
from acconeer.exptool.utils import USBDevice  # type: ignore[import]


@attrs.frozen(kw_only=True)
class ClientInfo:
    ip_address: Optional[str] = None
    serial_port: Optional[str] = None
    usb_device: Optional[Union[str, bool, USBDevice]] = None
    mock: Optional[bool] = None
    override_baudrate: Optional[int] = None

    @classmethod
    def _from_open(
        cls,
        ip_address: Optional[str] = None,
        serial_port: Optional[str] = None,
        usb_device: Optional[Union[str, bool, USBDevice]] = None,
        mock: Optional[bool] = None,
        override_baudrate: Optional[int] = None,
    ) -> ClientInfo:
        return ClientInfo(
            ip_address=ip_address,
            serial_port=serial_port,
            usb_device=usb_device,
            mock=mock,
            override_baudrate=override_baudrate,
        )

    def to_dict(self) -> dict[str, Any]:
        return attrs.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> ClientInfo:
        if d.get("usb_device") is not None:
            d = d.copy()
            d["usb_device"] = USBDevice.from_dict(d["usb_device"])
        return cls(**d)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> ClientInfo:
        return cls.from_dict(json.loads(json_str))

    def __str__(self) -> str:
        return "\n".join(
            [
                f"{type(self).__name__}",
                *pretty_dict_line_strs(self.to_dict()),
            ]
        )
