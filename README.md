# Warplink Setup
1. Clone WarpLink from the Github Distribution: https://github.com/warpware-distribution/warplink
2. Generating cmd/tlm files: from within WarpOS, go to the `build` directory and call `cmake ..`
   1. This will create a file called `cmd_tlm.json` within the build  directory
   2. Copy that file into the base directory of WarpLink
   3. Run `python3 CosmosUpdateCmdTlm.py`
      1. This will generate a `cmd.txt` and a `tlm.txt` used by the system
3. Call `./openc3.sh run`
   1. This builds the containers and activates the localhost GUI
4. To build the 'plugin' that ingests our commands and telemetry, use command: `cd openc3-cosmos-cfspp/ && ../openc3.sh cli rake build VERSION=1.0.0`
   1. Increment version (MAJOR.MINOR.MINOR)
   2. This creates a '.gem' file in this directory that we’ll use later: `openc3-cosmos-cfspp-#.#.#.gem`
5. On a webrowser, open http://localhost:2900/
   1. This opens the GUI for WarpLink
6. To install a new plugin, from the "Admin Console", select “Install from file” then select .gem file just created: `openc3-cosmos-cfspp-#.#.#.gem`
7. Depending on your setup, either follow the UDP, Linux Serial/USB, or Windows Serial/USB instructions for connecting to the telemetry stream

## Windows Serial/USB Command/Telemetry Interface
To run WarpLink using a telemetry connection over serial/USB, something called a “Bridge” needs to be created in order to connect the data coming in over the host machine’s COM port to the docker instance running under the hood.
Downloads needed:
* Download Ruby (v3.2+) from the official Ruby website.
* From Powershell, use command gem install openc3
  * Ensure Ruby gem executable path is in PATH environment variable
Configuration:
* In the base level directory of `warplink` is `bridge.txt`. There are a few configuration items to look at in here:
  * UART configuration (Baud rate, parity, data bits, flow control, etc)
  * COM port name
    * The com port you use for read and write is dependent on what com port your computer defines the USB connection as
  * Router port
    * Port used for the routing serial tlm to an internal TCP connection
* In the directory `warplink/openc3cosmos-cfspp` is the file for plugin.txt. This file has a line describing a TCP connection to host.docker.internal. Ensure this `INTERFACE` line is uncommented and all the other `INTERFACE` lines are commented out (serial and UDP)
  * If this was not commented out previously or you changed the plugin.txt, you will need to regenerate a ".gem" file and upload to the UI using instructions above
Once the new gem file is uploaded to the GUI and the device used to route telemetry is plugged in, all that is needed is to run the bridge command:
* From a PowerShell instance type the command openc3cli bridge bridge.txt.
* Expect a couple outputs to pop up in the terminal. You will know it succeeded if you get the output "SERIAL_ROUTER: Tcpip server accepted from host.docker.internal(...)"

## Linux Serial/USB Connection
To establish a connection to ta serial/USB device over Linux the user needs to configure `plugin.txt`. In the file, there is a line for `openc3/interfaces/serial_interface.py`. This line must be commented out to allow for transmission, and all other `INTERFACE` options commented out. The options for this are (in order) defined as:
* Write port
* Read port
* Baud Rate
* Parity
* Stop Bits
* Write Timeout
* Read Timeout

Ensure the serial configuration matches the hardware you have setup. Additionally, you will need to ensure that the  read/write ports you are using(default of/dev/ttyUSB0) matches whatever USB/serial you have plugged in.
* If you changed the plugin.txt, you will need to regenerate a gem file and upload to the UI using instructions above

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


### RasPi configuration for Serial-UDP
__NOTE: The Raspberry pi option is only used if you are attempting to route commands and telemetry through a Pi so your groundstation can send/receive data using a UDP connection.__

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
5. Plug in USB-C power supply
6. Wait for onboard LED to blink green
7. From a separate computer on the same network: `ssh <hostname>.local`
   1. If connection is not working, attempt to ping Pi
   2. On first boot, the RasPi may need to connect to the WiFi, so hang tight for ~10m if it’s not working right away
8. To set up the UDP connection on the RasPi:
   1. Modify the following file by changing the IP address and name in lines 40-41:
      1. cmd-tlm-interface.py
   2. Transfer the file to the RasPi (via VSCode remote-ssh extension, SFTP, or another method)
9. On the RasPi CLI: sudo python3 cmd-tlm-interface.py
   1.  You should start to see [UART RX] data streaming on stdout (if the serial input is sending telemetry)


## Troubleshooting

Most of the time, disconnecting then reconnecting (via the “Action” column on the CmdTlmServer tab) or rebuilding and reinstalling the plugin is a useful troubleshooting tool.
1. If no data iis appearing on the GUI and there are no reoccurring messages on the CmdTlmServer page
   1. Check that the Raspberry Pi is actually sending UDP data
      1. Verify the IP address, baud rate, and Serial port are correct on the Pi
   2. Ensure that the IP addresses are correct in your `openc3-cosmos-cfspp/plugin.txt`
2. If many "unknown" packets are arriving
   1. Reload your cmd_tlm.json from WarpOS, upload it to WarpLink, and follow the instructions for creating and loading the .gem file