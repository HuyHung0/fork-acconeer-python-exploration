# Copyright (c) Acconeer AB, 2023
# All rights reserved

from __future__ import annotations

import itertools
import operator
import typing as t

import attrs
import typing_extensions as te

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGraphicsSceneMouseEvent,
    QGridLayout,
    QLabel,
    QTabWidget,
    QToolTip,
    QWidget,
)

import pyqtgraph as pg

from acconeer.exptool import a121
from acconeer.exptool.a121.model import power
from acconeer.exptool.app.new.ui.resource_tab.event_system import (
    EventBroker,
    IdentifiedServiceUninstalledEvent,
)

from .distance_config_input import DistanceConfigEvent
from .session_config_input import SessionConfigEvent


_SECONDS_IF_RATE_UNSET = 2e-2
_DURATION_SB_DECIMALS = 4
_DURATION_SB_RANGE = (1e-4, 100)
_DURATION_SB_STEP = 5e-3

_X_AXIS_SPINBOX_LABEL = "X-axis length"

_A_to_mA = _s_to_ms = 1000


class PowerCurveBarGraphItem(pg.BarGraphItem):
    def __init__(self, power_profile: power.CompositeRegion) -> None:
        durations = [r.duration for r in power_profile.flat_iter()]
        starts = list(itertools.accumulate([0] + durations[:-1], operator.add))
        currents = [p.average_current for p in power_profile.flat_iter()]
        colors = [self._tag_color(p.tag) for p in power_profile.flat_iter()]

        super().__init__(
            x0=starts,
            width=durations,
            height=currents,
            brushes=colors,
        )
        self.setAcceptHoverEvents(True)

        self._power_profile = power_profile
        self._ends = [start + duration for start, duration in zip(starts, durations)]

    @staticmethod
    def _tag_color(tag: t.Optional[power.EnergyRegion.Tag]) -> str:
        if tag == power.EnergyRegion.Tag.MEASURE:
            return "cornflowerblue"
        if tag == power.EnergyRegion.Tag.OVERHEAD:
            return "red"
        if tag == power.EnergyRegion.Tag.CALIBRATION:
            return "orange"
        if tag == power.EnergyRegion.Tag.IDLE:
            return "forestgreen"
        if tag == power.EnergyRegion.Tag.COMMUNICATION:
            return "goldenrod"

        return "magenta"

    def _profile_description_at_point(self, x: float, y: float) -> str:
        for end, simple_profile in zip(self._ends, self._power_profile.flat_iter()):
            if x >= end:
                continue

            if y < simple_profile.current:
                return "\n".join(
                    [
                        simple_profile.description,
                        "",
                        "Current:",
                        f"    {simple_profile.current * _A_to_mA:.0f} mA",
                        "Duration:",
                        f"    {simple_profile.duration * _s_to_ms:.1f} ms",
                    ]
                )
            else:
                return ""

        return ""

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        x = event.pos().x()
        y = event.pos().y()
        global_pos = event.screenPos()
        tooltip = self._profile_description_at_point(x, y)

        # Work-around to be able to get tooltip-on-click and zoom with rectangle
        QTimer.singleShot(10, lambda: QToolTip.showText(global_pos, tooltip))
        super().mousePressEvent(event)

    def hoverEvent(self, event: t.Any) -> None:
        try:
            x = event.pos().x()
            y = event.pos().y()
        except Exception:
            return

        tooltip = self._profile_description_at_point(x, y)
        self.setToolTip(tooltip)


class _EnergyRegionPlot(QWidget):
    @attrs.frozen
    class _State:
        """Whenever this changes, the plot is redrawn (with the new information)"""

        profile_duration_s: float
        """This is controlled from a tab-local spinbox."""

        session_config: a121.SessionConfig
        """This received from events"""

        lower_power_state: t.Optional[power.Sensor.LowerPowerState]

    def __init__(
        self,
        profile_duration_s: float,
        session_config: a121.SessionConfig,
        lower_power_state: t.Optional[power.Sensor.LowerPowerState],
        algorithm: power.algo.Algorithm,
    ) -> None:
        super().__init__()

        self._state = self._State(profile_duration_s, session_config, lower_power_state)
        self._algorithm: te.Final[power.algo.Algorithm] = algorithm

        self._plot_widget = pg.plot()
        self._plot_widget.getPlotItem().setLabel("left", "Sensor + XM125", units="A")
        self._plot_widget.getPlotItem().setLabel("bottom", "Duration", units="s")
        self._plot_widget.getPlotItem().setContentsMargins(0, 0, 0, 10)
        self._plot_widget.getViewBox().setMouseMode(pg.ViewBox.PanMode)

        label = QLabel(_X_AXIS_SPINBOX_LABEL)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        self._duration_spinbox = QDoubleSpinBox()
        self._duration_spinbox.setRange(*_DURATION_SB_RANGE)
        self._duration_spinbox.setDecimals(_DURATION_SB_DECIMALS)
        self._duration_spinbox.setSingleStep(_DURATION_SB_STEP)
        self._duration_spinbox.setSuffix(" s")

        self._duration_spinbox.setValue(self._state.profile_duration_s)

        self._duration_spinbox.editingFinished.connect(
            lambda: self.evolve_current_state(profile_duration_s=self._duration_spinbox.value())
        )
        self._duration_spinbox.editingFinished.connect(self.plot_current_state)

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._plot_widget, 0, 0, 1, 2)
        layout.addWidget(label, 1, 0)
        layout.addWidget(self._duration_spinbox, 1, 1)
        self.setLayout(layout)

    def evolve_current_state(self, **kwargs: t.Any) -> None:
        self._state = attrs.evolve(self._state, **kwargs)

    def plot_current_state(self) -> None:
        session_profile = power.session(
            self._state.session_config,
            lower_power_state=self._state.lower_power_state,
            duration=self._state.profile_duration_s,
            algorithm=self._algorithm,
        )

        self._plot_widget.clear()

        bar_item = PowerCurveBarGraphItem(session_profile)
        self._plot_widget.addItem(bar_item)

        hline_item = pg.InfiniteLine(
            pos=session_profile.average_current,
            angle=0,
            pen={"color": "#222", "style": Qt.PenStyle.DashLine, "width": 2},
            label=f"Average current ({session_profile.average_current * _A_to_mA:.0f} mA)",
            labelOpts={"color": "#222"},
        )
        self._plot_widget.addItem(hline_item)

        self._plot_widget.setYRange(0, 0.1)


class EnergyRegionOutput(QTabWidget):
    INTERESTS: t.ClassVar[set[type]] = {
        SessionConfigEvent,
        IdentifiedServiceUninstalledEvent,
        DistanceConfigEvent,
    }
    description: t.ClassVar[str] = "\n\n".join(
        [
            "Visualizes a simulated power curve of a confiugration.",
            f"The spinbox {_X_AXIS_SPINBOX_LABEL!r} controls the end of the X-axis.",
            "Click and hold the plotted rectangles to get a description of that rectangle.",
        ]
    )
    window_title = "Power curve"

    def __init__(self, broker: EventBroker) -> None:
        super().__init__()

        self._tabs: dict[str, _EnergyRegionPlot] = {}
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("QTabBar { font: bold 14px; font-family: monospace; }")

        self.uninstall_function = broker.install_service(self)
        broker.brief_service(self)

    def handle_event(self, event: t.Any) -> None:
        if isinstance(event, SessionConfigEvent):
            self._handle_session_config_event(event)
        elif isinstance(event, DistanceConfigEvent):
            self._handle_distance_config_event(event)
        elif isinstance(event, IdentifiedServiceUninstalledEvent):
            self._handle_identified_service_uninstalled_event(event)
        else:
            raise NotImplementedError

    def _handle_session_config_event(self, event: SessionConfigEvent) -> None:
        if event.service_id not in self._tabs:
            configured_rate = power.configured_rate(event.session_config)
            if configured_rate is None:
                seconds_in_x_axis = _SECONDS_IF_RATE_UNSET
            else:
                seconds_in_x_axis = 1 / configured_rate

            plot_widget = _EnergyRegionPlot(
                seconds_in_x_axis,
                event.session_config,
                event.lower_power_state,
                power.algo.SparseIq(),
            )
            self._tabs[event.service_id] = plot_widget

            self.addTab(plot_widget, event.service_id)
        else:
            self._tabs[event.service_id].evolve_current_state(
                session_config=event.session_config,
                lower_power_state=event.lower_power_state,
            )

        self._tabs[event.service_id].plot_current_state()

    def _handle_distance_config_event(self, event: DistanceConfigEvent) -> None:
        session_config = event.translated_session_config

        if event.service_id not in self._tabs:
            configured_rate = power.configured_rate(event.translated_session_config)
            if configured_rate is None:
                seconds_in_x_axis = _SECONDS_IF_RATE_UNSET
            else:
                seconds_in_x_axis = 1 / configured_rate

            plot_widget = _EnergyRegionPlot(
                seconds_in_x_axis,
                session_config,
                event.lower_power_state,
                power.algo.Distance(),
            )
            self._tabs[event.service_id] = plot_widget

            self.addTab(plot_widget, event.service_id)
        else:
            self._tabs[event.service_id].evolve_current_state(
                session_config=session_config,
                lower_power_state=event.lower_power_state,
            )

        self._tabs[event.service_id].plot_current_state()

    def _handle_identified_service_uninstalled_event(
        self, event: IdentifiedServiceUninstalledEvent
    ) -> None:
        tab_widget = self._tabs.pop(event.id_)
        tab_index = self.indexOf(tab_widget)
        if tab_index != -1:
            self.removeTab(tab_index)
