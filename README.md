# mast-tests

This repository is to hold our new test suite as we develop it. Our old test suite will be phased out over a
period of time (timeline to be determined), but we need to make sure that these tests can be run outside of
our QA environment (in fact, we wish to be able to run these tests anywhere but the integration tests will still
require a live DataPower or more).

# Requirements for Running the Tests

1. MAST for IBM DataPower
2. Selenium's Python bindings

## MAST for IBM DataPower

If you have an active support contract, you should have been given a download link for the pre-built installer,
if not, you must build the installer yourself (not very difficult) just head over to our
[mast.installer github page](https://github.com/mcindi/mast.installer) and follow the instructions there.

## Selenium

Selenium can be installed with the following commands:

Linux

```
$ cd mast_home
$ set-env
$ pip install selenium
```

Windows

```
C:\> cd mast_home
C:\mast_home> set-env.bat
C:\mast_home> pip install selenium
```

# Running the tests

Currently there are only the integration tests available, more will become available as we phase out our old test
suite.

## Step 1

The first step is to edit the configuration file `config.json` and enter the appropriate values for your environment

__IMPORTANT__ Do __not__ run these tests against DataPower appliances which are being used for any other purpose
as the tests are rather intensive and will probably interupt normal operations

The important part of the configuration file is the `appliances` section, be sure to enter something which will
resolve through DNS and enter a valid username and password with privileged access.

## Step 2

Get MAST web up and running, you can do this by setting up mastd to run or by invoking the `mast-web` command line
utility.

## Step 3

In a new terminal navigate to the directory where the tests are located and enter the following command

```
python ui-tests.py
```

Logging output will go to stdout and a file by default, but this is configurable. In a future version the output will
be prettied up, but you can spot an error by the (often aggrivating but familiar) Python stack-trace which will be produced. 
