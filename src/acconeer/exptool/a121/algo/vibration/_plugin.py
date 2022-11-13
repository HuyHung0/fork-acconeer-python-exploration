# Copyright (c) Acconeer AB, 2022
# All rights reserved

from __future__ import annotations

from typing import Callable, Type

import numpy as np

from PySide6.QtWidgets import QWidget

import pyqtgraph as pg

import acconeer.exptool as et
from acconeer.exptool import a121
from acconeer.exptool.a121.algo._plugins import (
    ProcessorBackendPluginBase,
    ProcessorPlotPluginBase,
    ProcessorViewPluginBase,
)
from acconeer.exptool.a121.algo._utils import APPROX_BASE_STEP_LENGTH_M
from acconeer.exptool.a121.algo.vibration import (
    Processor,
    ProcessorConfig,
    ProcessorResult,
    get_sensor_config,
)
from acconeer.exptool.app.new import (
    AppModel,
    Message,
    PluginFamily,
    PluginGeneration,
    PluginSpecBase,
)
from acconeer.exptool.app.new.ui.plugin_components import PidgetFactoryMapping, pidgets


class BackendPlugin(ProcessorBackendPluginBase[ProcessorConfig, ProcessorResult]):
    @classmethod
    def get_processor_cls(cls) -> Type[Processor]:
        return Processor

    @classmethod
    def get_processor_config_cls(cls) -> Type[ProcessorConfig]:
        return ProcessorConfig

    @classmethod
    def get_default_sensor_config(cls) -> a121.SensorConfig:
        return get_sensor_config()


class ViewPlugin(ProcessorViewPluginBase[ProcessorConfig]):
    @classmethod
    def get_pidget_mapping(cls) -> PidgetFactoryMapping:
        # Note: Incomplete mapping
        return {
            "time_series_length": pidgets.IntParameterWidgetFactory(
                name_label_text="Time series length",
                limits=(0, None),
            ),
            "lp_coeff": pidgets.FloatSliderParameterWidgetFactory(
                name_label_text="Time filtering coefficient",
                suffix="",
                limits=(0, 1),
                decimals=2,
            ),
        }

    @classmethod
    def get_processor_config_cls(cls) -> Type[ProcessorConfig]:
        return ProcessorConfig


class PlotPlugin(ProcessorPlotPluginBase[ProcessorResult]):
    def __init__(self, *, plot_layout: pg.GraphicsLayout, app_model: AppModel) -> None:
        super().__init__(plot_layout=plot_layout, app_model=app_model)

    def setup(self, metadata: a121.Metadata, sensor_config: a121.SensorConfig) -> None:

        self.meas_dist_m = sensor_config.start_point * APPROX_BASE_STEP_LENGTH_M

        pen = et.utils.pg_pen_cycler(0)
        brush = et.utils.pg_brush_cycler(0)
        symbol_kw = dict(symbol="o", symbolSize=1, symbolBrush=brush, symbolPen="k")
        feat_kw = dict(pen=pen, **symbol_kw)
        symbol_dot_kw = dict(symbol="o", symbolSize=10, symbolBrush=brush, symbolPen="k")

        # precense plot
        self.precense_plot = pg.PlotItem()
        self.precense_plot.setMenuEnabled(False)
        self.precense_plot.showGrid(x=False, y=True)
        self.precense_plot.setLabel("left", "Max amplitude")
        self.precense_plot.setLabel("bottom", "Distance (m)")
        self.precense_plot.setXRange(self.meas_dist_m - 0.001, self.meas_dist_m + 0.001)
        self.precense_curve = self.precense_plot.plot(**dict(pen=pen, **symbol_dot_kw))

        self.smooth_max_precense = et.utils.SmoothMax(tau_decay=10.0)

        # sweep and threshold plot
        self.time_series_plot = pg.PlotItem()
        self.time_series_plot.setMenuEnabled(False)
        self.time_series_plot.showGrid(x=True, y=True)
        self.time_series_plot.setLabel("left", "Displacement (mm)")
        self.time_series_plot.setLabel("bottom", "History")
        self.time_series_curve = self.time_series_plot.plot(**feat_kw)

        sublayout = self.plot_layout.addLayout(row=0, col=0)
        sublayout.layout.setColumnStretchFactor(1, 5)
        sublayout.addItem(self.precense_plot, row=0, col=0)
        sublayout.addItem(self.time_series_plot, row=0, col=1)

        self.smooth_lim_time_series = et.utils.SmoothLimits(tau_decay=0.5, tau_grow=0.1)

        self.fft_plot = self.plot_layout.addPlot(col=0, row=1)
        self.fft_plot.setMenuEnabled(False)
        self.fft_plot.showGrid(x=True, y=True)
        self.fft_plot.setLabel("left", "Power (db)")
        self.fft_plot.setLabel("bottom", "Frequency (Hz)")
        self.fft_plot.addItem(pg.PlotDataItem())
        self.fft_curve = self.fft_plot.plot(**feat_kw)

        self.smooth_max_fft = et.utils.SmoothMax()

    def update(self, processor_result: ProcessorResult) -> None:

        time_series = processor_result.time_series
        z_abs_db = processor_result.lp_z_abs_db
        freqs = processor_result.freqs
        max_amplitude = processor_result.max_amplitude

        self.precense_curve.setData([self.meas_dist_m], [max_amplitude])
        lim = self.smooth_max_precense.update(max_amplitude)
        self.precense_plot.setYRange(0, max(1000.0, lim))

        self.time_series_curve.setData(time_series)
        lim = self.smooth_lim_time_series.update(time_series)
        self.time_series_plot.setYRange(lim[0], lim[1])

        self.fft_curve.setData(freqs, z_abs_db)
        lim = self.smooth_max_fft.update(np.max(z_abs_db))
        self.fft_plot.setYRange(0, lim)


class PluginSpec(PluginSpecBase):
    def create_backend_plugin(
        self, callback: Callable[[Message], None], key: str
    ) -> BackendPlugin:
        return BackendPlugin(callback=callback, generation=self.generation, key=key)

    def create_view_plugin(self, app_model: AppModel, view_widget: QWidget) -> ViewPlugin:
        return ViewPlugin(app_model=app_model, view_widget=view_widget)

    def create_plot_plugin(
        self, app_model: AppModel, plot_layout: pg.GraphicsLayout
    ) -> PlotPlugin:
        return PlotPlugin(app_model=app_model, plot_layout=plot_layout)


VIBRATION_PLUGIN = PluginSpec(
    generation=PluginGeneration.A121,
    key="vibration",
    title="Vibration measurement",
    description="Quantify the frequency content of vibrating object.",
    family=PluginFamily.EXAMPLE_APP,
)