# OpenC3 COSMOS Project

This git repo is used as a starting point for running and configuring OpenC3 COSMOS for your specific project.
It includes the necessary scripts to run OpenC3 COSMOS, but does not come with all the source code and relies on
running released containers rather than building containers from source. This is the recommended starting
place for any project who wants to use OpenC3 COSMOS, but not develop the core system.

## Quick Start

1. git clone https://github.com/openc3/cosmos-project.git cosmos-myprojectname
2. Edit .env and change OPENC3_TAG to the specific version you would like to run (ie. OPENC3_TAG=6.4.1)
   1. This will allow you to upgrade versions when you choose rather than following latest
3. Start OpenC3 COSMOS
   1. On Linux/Mac: ./openc3.sh run
   2. On Windows: openc3.bat run
4. After approximately 2 minutes, open a web browser to http://localhost:2900
   1. If you run "docker ps", you can watch until the openc3-init container completes, at which point the system should be fully configured and ready to use.

## Run without the Demo project

1. Edit .env and remove the OPENC3_DEMO line
2. If you have already ran with the demo also uninstall the demo plugin from the Admin tool.

## Upgrade to a Specific Version

1. Stop OpenC3
   1. On Linux/Mac: ./openc3.sh stop
   2. On Windows: openc3.bat stop
2. Edit .env and change OPENC3_TAG to the specific version you would like to run (ie. OPENC3_TAG=6.4.1)
3. Start OpenC3
   1. On Linux/Mac: ./openc3.sh run
   2. On Windows: openc3.bat run

NOTE: Downgrades are not necessarily supported. When upgrading COSMOS we need to upgrade databases and sometimes migrate internal data structures. While we perform a full regression test on every release, we recommend upgrading an individual machine with your specific plugins and do local testing before rolling out the upgrade to your production system.

## Change all default credentials and secrets

1. Edit .env and change:
   1. SECRET_KEY_BASE
   2. OPENC3_SERVICE_PASSWORD
   3. OPENC3_REDIS_PASSWORD
   4. OPENC3_BUCKET_PASSWORD
   5. OPENC3_SR_REDIS_PASSWORD
   6. OPENC3_SR_BUCKET_PASSWORD
2. Edit ./openc3-redis/users.acl and change the password for each account. Note passwords for openc3/scriptrunner must match the REDIS passwords in the .env file:
   1. openc3
   2. admin
   3. scriptrunner

Passwords stored in `./openc3-redis/users.acl` use a sha256 hash.
To generate a new hash use the following method, and then copy / paste into users.acl

```bash
echo -n 'adminpassword' | openssl dgst -sha256
SHA2-256(stdin)= 749f09bade8aca755660eeb17792da880218d4fbdc4e25fbec279d7fe9f65d70
```

## Opening to the Network

Important: Before exposing OpenC3 COSMOS to any network, even a local network, make sure you have changed all default credentials and secrets!!!

### Open to the network using https/SSL and your own certificates

1. Copy your public SSL certicate to ./openc3-traefik/cert.crt
2. Copy your private SSL certicate to ./openc3-traefik/cert.key
3. Edit compose.yaml
   1. Comment out this openc3-traefik line: `- "./openc3-traefik/traefik.yaml:/etc/traefik/traefik.yaml:z"`
   2. Uncomment this openc3-traefik line: `- "./openc3-traefik/traefik-ssl.yaml:/etc/traefik/traefik.yaml"`
   3. Uncomment this openc3-traefik line: `- "./openc3-traefik/cert.key:/etc/traefik/cert.key"`
   4. Uncomment this openc3-traefik line: `- "./openc3-traefik/cert.crt:/etc/traefik/cert.crt"`
4. If you are able to run as the standard browser ports 80/443, edit compose.yaml:
   1. Comment out this openc3-traefik line: `- "127.0.0.1:2900:2900"`
   2. Comment out this openc3-traefik line: `- "127.0.0.1:2943:2943"`
   3. Uncomment out this openc3-traefik line: `- "80:2900"`
   4. Uncomment out this openc3-traefik line: `- "443:2943"`
5. If not, edit compose.yaml:
   1. Remove 127.0.0.1 from this line: `- "127.0.0.1:2900:2900"`
   2. Remove 127.0.0.1 from this line: `- "127.0.0.1:2943:2943"`
6. Edit ./openc3-traefik/traefik-ssl.yaml
   1. Update line 14 to the first port number in step 4 or 5: to: ":2943" # This should match port forwarding in your compose.yaml
   2. Update line 22 to your domain: - main: "mydomain.com" # Update with your domain
7. Start OpenC3
   1. On Linux/Mac: ./openc3.sh run
   2. On Windows: openc3.bat run
8. After approximately 2 minutes, open a web browser to `https://<Your IP Address>` (or `https://<Your IP Address>:2943` if you can't use standard ports)
   1. If you run "docker ps", you can watch until the openc3-init container completes, at which point the system should be fully configured and ready to use.

### Open to the network using a global certificate from Let's Encrypt

Warning: These directions only work when exposing OpenC3 to the internet. Make sure you understand the risks and have properly configured your server settings and firewall.

1. Make sure that your DNS settings are mapping your domain name to your server
2. Edit compose.yaml
   1. Comment out this openc3-traefik line: `- "./openc3-traefik/traefik.yaml:/etc/traefik/traefik.yaml:z"`
   2. Uncomment this openc3-traefik line: `- "./openc3-traefik/traefik-letsencrypt.yaml:/etc/traefik/traefik.yaml"`
3. Edit compose.yaml:
   1. Comment out this openc3-traefik line: `- "127.0.0.1:2900:2900"`
   2. Comment out this openc3-traefik line: `- "127.0.0.1:2943:2943"`
   3. Uncomment out this openc3-traefik line: `- "80:2900"`
   4. Uncomment out this openc3-traefik line: `- "443:2943"`
4. Start OpenC3
   1. On Linux/Mac: ./openc3.sh run
   2. On Windows: openc3.bat run
5. After approximately a few minutes, open a web browser to `https://<Your Domain Name>`
   1. If you run "docker ps", you can watch until the openc3-init container completes, at which point the system should be fully configured and ready to use.

### Open to the network insecurely using http

Warning: This is not recommended except for temporary testing on a local network. This will send plain text passwords over the network!

1. Edit compose.yaml
   1. Comment out this openc3-traefik line: `- "./openc3-traefik/traefik.yaml:/etc/traefik/traefik.yaml:z"`
   2. Uncomment this openc3-traefik line: `- "./openc3-traefik/traefik-allow-http.yaml:/etc/traefik/traefik.yaml"`
   3. Remove 127.0.0.1 from this line: `- "127.0.0.1:2900:2900"`
2. Start OpenC3
   1. On Linux/Mac: ./openc3.sh run
   2. On Windows: openc3.bat run
3. After approximately 2 minutes, open a web browser to `https://<Your IP Address>:2900`
   1. If you run "docker ps", you can watch until the openc3-cosmos-init container completes, at which point the system should be fully configured and ready to use.


## To Build new commands and Telem and run

1. From the base amanserver directory, add in a "cmd_tlm.json" file (generated by a call to cmake in the WarpOS directory, and then copied over).
2. Run the CosmosUpdateCmdTlm.py file
   1. New command and telemetry targets should then be generated in the openc3-cosmos-cfspp directory
3. "cd" into the openc3-cosmos-cfspp directory
4. Call "$../openc3.sh cli rake build VERSION=X.X.X
   1. This will generate a new .gem file within the same directory
5. In the Graphical web interface running for warplink, go to "Admin Console" and "Install from file", selecting the new gem file created

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


## Using a Raspberry Pi for telemetry

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


## Flashing the SD card for the RasPi

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