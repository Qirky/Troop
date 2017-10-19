# Troop v0.5

## Real-time collaborative live coding

Troop is a real-time collaborative tool that enables group live coding within the same document across multiple computers. Hypothetically Troop can talk to any interpreter that can take input as a string from the command line but it is already configured to work with live coding languages [FoxDot](https://github.com/Qirky/FoxDot), and [TidalCycles](https://tidalcycles.org/). 

Troop is not a language for live coding but a tool for connecting multiple live coders over a network - so you'll need to install your language of choice before you get started. By default Troop runs with the Python based language, [FoxDot](https://github.com/Qirky/FoxDot), but it can also be used with [TidalCycles](https://tidalcycles.org/). Click the links to find out more about installing. Both of these require the audio engine [SuperCollider](http://supercollider.github.io/) to work.

Troop is compatible with both Python 2 and 3, which can be downloaded from [here](https://www.python.org/) (see **troubleshooting** below for more help on installing Python) but make sure that you use the same version of Python that use to run [FoxDot](https://github.com/Qirky/FoxDot) when doing so.

## Getting started

Download the files from this repository as a .zip file and extract the contents to a suitable folder. Alternatively, if you are familiar with Git you can clone the repository yourself using:

	git clone https://github.com/Qirky/Troop.git

and keep up to date with the project by using `git pull -a`, which automatically update your files with any changes. 

## Running the Troop server

Troop is a client-server application, which means that you need to run a Troop server on a machine that other people on the network using the client (interface) can connect to. Only one person needs to run the server, so decide who will do the "hosting" before getting started. 

Start the Troop Server by running the `run-server.py` Python file. Depending on your O/S and Python installation you can either double click the file or run it from the command prompt. To run from the command prompt you'll need to make sure you're in correct directory: use the 'cd' command followed by the path to where you've extracted Troop. For example if Troop is saved in C:\Users\Guest\Troop then type the following into the command prompt:

	cd C:\Users\Guest\Troop
	
Then to run the server application, type in the following and press return:

	python run-server.py

You will be asked to enter a password. You can leave this blank if you wish - but make sure you are on a secure network if you do. Connecting clients will be required to enter the same password when connecting to the server. By default the server will run on port 57890 but this isn't always the case. Make a note of the address and port number so that Troop clients can connect to the server and you're up and running! To stop the server, either close the terminal window it's running in or use the keyboard shorcut `Ctrl+C` to kill the process. 

**Warning:** Code executed by one client is executed on every client, so be careful when using public networks as you will then be susceptible to having malicious code run on your machine. Avoid using public networks and only give your server password to people you trust.

### Running the Troop Client

To run the client file in its default FoxDot mode you can either double click the `run-client.py` file or run it via the command line as you would do with the server but using:

	python run-client.py

To run Troop in TidalCycles mode you need to specify this using the "mode" flag like so:

	python run-client.py --mode TidalCycles

You can change the language after you've opened the editor by going to `Code -> Choose Language` and selecting the language of choice.  

On running this script you will be asked for four things:

- The IP address of the Troop Server
- The port of the Troop Server
- A name you wish to be identified by while using Troop
- The password for the Troop Server

If you've connected successfully then you'll greeted with an interface with three boxes. The largest of the boxes is used to input code and the others to display console responses and some stats about character usages. To evaluate a line of code make sure your text cursor is placed in the line you want and press `Ctrl+Return`. If there are any other users connected you should see coloured markers in the text displaying their names. You can even execute code they've written and vice versa.

You can create a `client.cfg` file in the root directory if you have a host / port that you want to connect to regularly. It's contents should contain two lines:

	host=<hostname_or_ip_address>
	port=<port_number>  


## Troubleshooting

### Installing Python

If you are using Windows you might get an error along the lines of "python is not recognized command". This means you need to add Python to your system path so that your computer knows where to find Python's libraries. To do this open file explorer and right click on My Computer / This PC and click properties. From here you should open Advanced System Properties and click the button labelled Environment Variables. There should be a list of variables and their value. Of these variables there should be one named PATH. Edit it and add the location where Python was installed, most likely C:\Python27. If the PATH variable does not exist, create it and set its value to the Python installation.

### Server says it is running on 127.0.0.1

For some versions of Linux Python retrieves the localhost IP address instead of the public facing IP address, which means users trying to connect to 127.0.0.1 when running the Troop client will attempt to connect to *their own machine*. To find your IP address, open a terminal/command prompt and type `ipconfig` (windows) or `ifconfig` (Linux/Mac) and press enter. This will display information about your network adapters and your IP address will probably look along the lines of 192.168.0.xx if you are using a standard home network.  

### Errors or bugs while Troop is running

If you do find any problems when using Troop, please raise an issue on the GitHub page quoting the error message and describing what you were doing at the time (on Troop not in life).


## Thanks

Huge thank you to Alex McLean for his inspiration for this project and to Lucy and Laurie for testing it during its development. 