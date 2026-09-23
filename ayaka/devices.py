from collections.abc import Iterable, Mapping
from typing import Any


def choose_input_device(
    devices: Iterable[Mapping[str, Any]],
    *,
    name: str,
    hostapi: str,
    device_index: int | None = None,
) -> Mapping[str, Any]:
    candidates = [
        device for device in devices
        if int(device.get("max_input_channels", 0)) > 0
        and (not name or name.casefold() in str(device.get("name", "")).casefold())
        and (not hostapi or hostapi.casefold() in str(device.get("hostapi", "")).casefold())
    ]
    if device_index is not None:
        candidates = [d for d in candidates if d.get("index") == device_index]
    if not candidates:
        raise ValueError(
            f"No input device matched name={name!r}, hostapi={hostapi!r}, index={device_index!r}"
        )
    return candidates[0]


def query_wasapi_input(audio_config):
    """Resolve the configured device through sounddevice on Windows."""
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError("sounddevice is required for microphone capture") from exc

    hostapis = sd.query_hostapis()
    hostapi_names = {index: item["name"] for index, item in enumerate(hostapis)}
    devices = []
    for index, raw in enumerate(sd.query_devices()):
        item = dict(raw)
        item["index"] = index
        item["hostapi"] = hostapi_names.get(item.get("hostapi"), "")
        devices.append(item)
    return choose_input_device(
        devices,
        name=audio_config.device_name,
        hostapi=audio_config.hostapi_name,
        device_index=audio_config.device_index,
    )
