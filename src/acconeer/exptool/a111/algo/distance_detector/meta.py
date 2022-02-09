from acconeer.exptool.a111.algo import ModuleFamily, ModuleInfo
from acconeer.exptool.a111.algo.utils import multi_sensor_pg_updater, multi_sensor_processor

from .plotting import PGUpdater
from .processing import Processor, get_processing_config, get_sensor_config


module_info = ModuleInfo(
    key="envelope_distance",
    label="Distance Detector (envelope)",
    pg_updater=multi_sensor_pg_updater(PGUpdater),
    processing_config_class=get_processing_config,
    module_family=ModuleFamily.DETECTOR,
    sensor_config_class=get_sensor_config,
    processor=multi_sensor_processor(Processor),
    multi_sensor=True,
    docs_url=(
        "https://acconeer-python-exploration.readthedocs.io/"
        + "en/latest/processing/distance_detector.html"
    ),
)
