# Troop v0.9.6

## Real-time collaborative live coding

Troop is a real-time collaborative tool that enables group live coding within the same document across multiple computers. Hypothetically Troop can talk to any interpreter that can take input as a string from the command line but it is already configured to work with live coding languages [FoxDot](https://github.com/Qirky/FoxDot), [TidalCycles](https://tidalcycles.org/), and [SuperCollider](http://supercollider.github.io/). 

Troop is not a language for live coding but a tool for connecting multiple live coders over a network - so you'll need to install your language of choice before you get started. By default Troop runs with the Python based language, [FoxDot](https://github.com/Qirky/FoxDot), but it can also be used with [TidalCycles](https://tidalcycles.org/) and [SuperCollider](http://supercollider.github.io/). Click the links to find out more about installing. Both TidalCycles and FoxDot require [SuperCollider](http://supercollider.github.io/) to work, so it's a good bet you'll need it.

Troop is compatible with both Python 2 and 3, which can be downloaded from [here](https://www.python.org/) (see **troubleshooting** below for more help on installing Python) but make sure that you use the same version of Python that use to run [FoxDot](https://github.com/Qirky/FoxDot) when doing so.

Linux users may need to install `python-tk` if you have not done so already:

`apt-get install python-tk`

## Getting started

There are two ways of using Troop; one is to download the latest release and run it as you would any other program on your computer, and the other is two run the files using Python. The first option does not require Python to be installed on your machine, but you do need to have correctly configured your live coding language of choice first e.g. FoxDot, which uses Python to run.

#### Using the downloadable executable

1. Download the latest version for your appropriate operating system [from this page](https://github.com/Qirky/Troop/releases).
2. Double-click the program to get started. Enter server connection details then press OK to open the interface.
3. You can still run Troop from the command line with extra arguments as you would the Python files. Run the following command to find out more (changing the executable name for the version you have downloaded):

	Troop-Windows-0.9.1-client.exe -h

See "Running the Troop client" below for more details.

#### Running the Python files

Download the files from this repository as a .zip file and extract the contents to a suitable folder. Alternatively, if you are familiar with Git you can clone the repository yourself using:

	git clone https://github.com/Qirky/Troop.git

and keep up to date with the project by using `git pull -a`, which automatically update your files with any changes. 

## Running the Troop server

Troop is a client-server application, which means that you need to run a Troop server on a machine that other people on the network using the client (interface) can connect to. Only one person needs to run the server, so decide who will do the "hosting" before getting started. 

Start the Troop Server by running the `run-server.py` Python file. Depending on your O/S and Python installation you can either double click the file or run it from the command prompt. To run from the command prompt you'll need to make sure you're in correct directory: use the 'cd' command followed by the path to where you've extracted Troop. For example if Troop is saved in `C:\Users\Guest\Troop` then type the following into the command prompt:

	cd C:\Users\Guest\Troop
	
Then to run the server application, type in the following and press return:

	python run-server.py

If you don't have Python installed and you have downloaded the executable, simply type the name of the executable and press return (or double clicking on it):

	Troop-Windows-0.9.1-server.exe

You will be asked to enter a password. You can leave this blank if you wish - but make sure you are on a secure network if you do. Connecting clients will be required to enter the same password when connecting to the server. By default the server will run on port 57890 but this isn't always the case. Make a note of the address and port number so that Troop clients can connect to the server and you're up and running! To stop the server, either close the terminal window it's running in or use the keyboard shorcut `Ctrl+C` to kill the process. 

**Warning:** Code executed by one client is executed on every client, so be careful when using public networks as you will then be susceptible to having malicious code run on your machine. Avoid using public networks and only give your server password to people you trust.

### Running the Troop Client

Once you've opened the Troop client you'll be able to enter the IP address and port number of the Troop server instance running on your network. Enter the name you want to display and the password for the server and select the interpreter you want to use (requires installation and setup - see below). Press OK to open the editor. You can also change the interpreter to use with Troop after you've opened the editor by going to `Code -> Choose Language` and selecting the language of choice.

Alternatively you can start Troop in a different "mode" so that it is interpreting another language at startup. To do this, run the following from the command line depending on your desired startup language:
 
**[TidalCycles](https://tidalcycles.org/)**

	python run-client.py --mode TidalCycles

**TidalCycles (installed using Stack)**

	python run-client.py --mode TidalCyclesStack

**[SuperCollider](https://supercollider.github.io/)**

	python run-client.py --mode SuperCollider

To use the SuperCollider language from Troop you will need to install the Troop Quark but opening SuperCollider and running the following line of code. This will create a class that listens for messages from Troop containing SuperCollider code.

	Quarks.install("http://github.com/Qirky/TroopQuark.git")

Once this is done you'll need to make SuperCollider listen for Troop messages by evaluating the following line of code in SuperCollider:

	Troop.start
  
**[Sonic Pi](https://sonic-pi.net/)**

	python run-client.py --mode SonicPi  

Requires Sonic-Pi to be open on your computer.

**Other**

	python run-client.py --mode path/to/interpreter

If you've connected successfully then you'll greeted with an interface with three boxes. The largest of the boxes is used to input code and the others to display console responses and some stats about character usages. To evaluate a line of code make sure your text cursor is placed in the line you want and press `Ctrl+Return`. If there are any other users connected you should see coloured markers in the text displaying their names. You can even execute code they've written and vice versa.

#### Running multiple instances in the same location

If you are and your fellow live coders are in the same room using Troop, it's often most convenient for only one laptop to produce sound (the master). When one user logs in using an interpreter, such as TidalCycles, all others can log in using the "No Interpreter" option or `--mode none` flag. When the "master" laptop receives text in the console, it is sent to all of the other users so you can see exactly what your code  is doing. Futhermore, you can select the language for syntax highlighting / keyboard short-cuts at the log in window or use the `--syntax` flag to choose the language you wish to emulate.

#### Other flags

Other flags can be added to the `run-client.py` command too. Below is an in-depth look at how to use them:

`python run-client.py -h` / `python run-client.py --help` - Shows the help dialog and exits

`python run-client.py -i` / `python run-client.py --cli` - Starts Troop with a command line interface

`python run-client.py -H HOST` / `python run-client.py --host HOST` - Start Troop with the host value set to HOST

`python run-client.py -P port` / `python run-client.py --port PORT` - Start Troop with the port value set to PORT

`python run-client.py -m MODE` / `python run-client.py --mode MODE` - Start Troop with the specified mode (see above)

`python run-client.py -c` / `python run-client.py --config` - Load host/port info from `client.cfg`. You can create a `client.cfg` file in the root directory if you have a host / port that you want to connect to regularly. It's contents should contain two lines:

	host=<hostname_or_ip_address>
	port=<port_number>  

`python run-client.py -a ARG1, ARG2, ...` / `python run-client.py --args ARG1, ARG2, ...` - Supply remaining command line arguments to the interpreter e.g.

	python run-client.py --args --startup path/to/startup_file.py

## Troubleshooting

### Installing Python

If you are using Windows you might get an error along the lines of "python is not recognized command". This means you need to add Python to your system path so that your computer knows where to find Python's libraries. To do this open file explorer and right click on My Computer / This PC and click properties. From here you should open Advanced System Properties and click the button labelled Environment Variables. There should be a list of variables and their value. Of these variables there should be one named PATH. Edit it and add the location where Python was installed, most likely C:\Python27. If the PATH variable does not exist, create it and set its value to the Python installation.

### Server says it is running on 127.0.0.1

For some versions of Linux Python retrieves the localhost IP address instead of the public facing IP address, which means users trying to connect to 127.0.0.1 when running the Troop client will attempt to connect to *their own machine*. To find your IP address, open a terminal/command prompt and type `ipconfig` (windows) or `ifconfig` (Linux/Mac) and press enter. This will display information about your network adapters and your IP address will probably look along the lines of 192.168.0.xx if you are using a standard home network.  

### Errors or bugs while Troop is running

If you do find any problems when using Troop, please raise an issue on the GitHub page quoting the error message and describing what you were doing at the time (on Troop not in life).


## Thanks

Huge thank you to Alex McLean for his inspiration for this project and to Lucy and Laurie, among other users from the live coding community, for testing it during its development. 

### Feedback

Your feedback for this project would be greatly appreciated. If you have used the Troop software yourself, please take a few minutes to fill out my (mostly) multiple-choice [online questionnaire](http://tinyurl.com/troop-feedback).
