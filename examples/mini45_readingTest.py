import nidaqmx
from nidaqmx.constants import TerminalConfiguration
import time

with nidaqmx.Task() as task:
    channels = [f"Dev1/ai{i}" for i in range(6)]
    for ch in channels:
        task.ai_channels.add_ai_voltage_chan(
            ch,
            terminal_config=TerminalConfiguration.RSE,  # Single-ended input; (RSE)
            min_val=0.0,    # minimum voltage
            max_val=5.0     # max voltage
        )

    print(f"Reading {len(channels)} channels: {', '.join(channels)}")
    print("Press Ctrl+C to stop...\n")

    try:
        while True:
            # read the instantaneous voltages from all channels at once
            voltages = task.read()  # return a list of six floats
            # print voltages with channel labels
            voltage_str = "  ".join([f"ai{i}: {v:.4f} V" for i, v in enumerate(voltages)])
            print(voltage_str)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopped by user.")
