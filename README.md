# OpenC3 COSMOS Setup

1. Clone WarpLink
2. From within WarpOS, go to the `build` directory and call `cmake ..`
   1. This will create a file called `cmd_tlm.json` within the build  directory
   2. Copy that file into the base directory of WarpLink
   3. Run `python3 CosmosUpdateCmdTlm.py`
      1. This will generate a `cmd.txt` and a `tlm.txt` used by the system
3. Call `./openc3.sh run`
   1. This activates the localhost for later
   2. Should only need to do this the first time you set up, unless you send a stop command
4. `cd openc3-cosmos-cfspp/ && ../openc3.sh cli rake build VERSION=1.0.0`
   1. Increment version (MAJOR.MINOR.MINOR)
   2. This creates a file in this directory that we’ll use later: `openc3-cosmos-cfspp-#.#.#.gem`
5. On a webrowser, open http://localhost:2900/
   1. This opens the GUI for WarpLink
6. Delete the existing "plugin"
   1. Assuming the current plugin is “demo”: click on "Admin Console" → "demo" → “…” icon → trash icon to delete
   2. If there is nothing under "Installed Plugins", skip this step
7. To install a new plugin, from the "Admin Console", select “Install from file” then select .gem file just created: `openc3-cosmos-cfspp-#.#.#.gem`

## Using a serial/USB connection for command/telemetry
## Using a Raspberry Pi for command/telemetry

The simplest method to receive telemetry is over wifi using a RasPi. You can either:
1. Use the Raspberry Pi as a passthrough for telemetry
   1. Connect the Telemetry UART from the HW to the Pi.
   2. Upload the `cmd-tlm-interface.py` file to the pi, and ensure the configuration items are updated correctly
      1. Specifically, the arguments at the beginning of main for which USB, which IP, and the UART rate.
   3. Run `cmd-tlm-interface.py`, either with the correct defaults described above or with the correct option flags
      1. Telemetry should start passing through
2. Use the Raspberry Pi as the hardware platform and configure the platform to take telemetry and send it over a socket
**Notes**:
1. The system is currently only configured to take in telemetry from UDP port 5005 and send commands on port 5006.
2. In WarpLink, in the file `openc3-cosmos-cfspp/plugin.txt`, ensure the IP listed after openc3/interfaces/udp_interface.py is the IP of the Pi you are running


### Flashing the SD card for the RasPi

If the RasPi hasn’t been flashed yet:
1. Download the RPi Imager
2. Plug SD card into your computer
3. Config
   1. Operating System: RPi OS 64-bit
   2. Storage: Internal SD card reader (or whatever your specific SD card interface is)
   3. Settings (gear icon):
      1. Set hostname to your liking
      2. Check enable SSH and “Use password authentication”
      3. Choose a username
      4. Configure wireless LAN per your internet, ensure the password is correct
   4. Click ‘Write’ then ‘yes’
4. Once write operation is complete and a dialog box tells you it’s okay to do so, unplug the SD card and transfer it to the RasPi


## Troubleshooting

Most of the time, disconnecting then reconnecting (via the “Action” column on the CmdTlmServer tab) or rebuilding and reinstalling the plugin is a useful troubleshooting tool.
1. If no data iis appearing on the GUI and there are no reoccurring messages on the CmdTlmServer page
   1. Check that the Raspberry Pi is actually sending UDP data
      1. Verify the IP address, baud rate, and Serial port are correct on the Pi
   2. Ensure that the IP addresses are correct in your `openc3-cosmos-cfspp/plugin.txt`
2. If only "unknown" packets are arriving
   1. Reload your cmd_tlm.json from WarpOS, upload it to WarpLink, and follow the instructions for creating and loading the .gem file
3. If there are significant errors of incorrect length packets:
   1. Reload your cmd_tlm.json from WarpOS, upload it to WarpLink, and follow the instructions for creating and loading the .gem file