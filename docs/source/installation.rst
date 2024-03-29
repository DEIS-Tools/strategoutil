..    include:: <isonum.txt>

.. _installation:

==================
Installation guide
==================

This part of the documentation provides detailed instruction on the installation of *strategoutil*
and UPPAAL Stratego.

Strategoutil
------------

*strategoutil* is available through pip:

.. code-block:: sh

  pip install strategoutil

Now *strategoutil* can be directly used in python with

.. code-block:: python

  import strategoutil

UPPAAL Stratego
---------------

*strategoutil* cannot run without an installation of UPPAAL Stratego itself. *strategoutil* comes not
with UPPAAL Stratego, so you have to install this by yourself. Follow the instructions below for the
recommended way of installing UPPAAL Stratego for different operation systems.

.. note:: Since UPPAAL 5, UPPAAL Stratego is part of UPPAAL itself. It is recommended to download UPPAAL 5
  instead of UPPAAL Stratego. The installation instructions below still apply for UPPAAL 5.

Linux
^^^^^

Go to the `download page <https://uppaal.org/downloads/>`_ of UPPAAL
Stratego. On this page, choose the latest release and the right build (32-bit versus 64 bit Linux
version). If you are doubting about your OS version, go to *Settings* |rarr| *about* |rarr| *OS Type*.
After accepting the license, the download should start.

Open a terminal and move to the folder where UPPAAL Stratego has been downloaded to. Now we will
unzip the file with

.. code-block:: sh

  unzip <name of uppaal stratego file>.zip -d $HOME/.local/bin

where ``<name of uppaal stratego file>.zip`` is the name of the downloaded file (depending on the version
you downloaded), for example ``uppaal-4.1.20-stratego-9-linux64.zip``.

Navigate to the ``$HOME/.local/bin`` folder with

.. code-block:: sh

  cd $HOME/.local/bin

and verify that UPPAAL Stratego has been unzipped correctly to this folder with

.. code-block:: sh

  ls

and look for a folder named ``<name of uppaal stratego file>``.

Now we will create a symbolic link to the UPPAAL Stratego engine:

.. code-block:: sh

  ln -s <name of uppaal stratego file>/bin/verifyta <short name>

``<short name>`` can be any name you like, but it will become the command that you (and, in fact,
*strategoutil*) call from a terminal. The suggestion is to always include the version number of the
downloaded UPPAAL Stratego. For example, if you downloaded ``uppaal-4.1.20-stratego-9-linux64.zip``,
then ``verifyta-stratego-9`` can be a good name, and the full command for the symbolic link becomes

.. code-block:: sh

  ln -s uppaal-4.1.20-stratego-9-linux64/bin/verifyta verifyta-stratego-9

.. note:: In UPPAAL Stratego versions 7 and lower, the folder structure was slightly different.
  For these lower versions you need to create the symbolic link with:

  .. code-block:: sh

    ln -s <name of uppaal stratego file>/bin-Linux/verifyta <short name>

Verify that the symbolic link is created correctly by typing

.. code-block:: sh

  ls -l

and check that the symbolic link is not colored red, i.e., red indicates that the link is broken.

Finally, we check whether the symbolic link we created is recognized anywhere in the system. First,
navigate to another random folder, for example your home folder

.. code-block:: sh

  cd

and type

.. code-block:: sh

  <short name> -h

with the short name of the symbolic link, for example ``verifyta-stratego-9``. The command line
manual of UPPAAL Stratego should now be printed. If so, we are ready to go. Otherwise, look at
:ref:`installation_problems`.

Windows
^^^^^^^

.. todo:: No instructions yet.

MacOS
^^^^^

Go to the `download page <https://uppaal.org/downloads/>`_ of UPPAAL
Stratego. On this page, choose the latest release and the right build.
After accepting the license, the download should start.

Unzip the downloaded file. As a result, you should now have a ``.app`` file.
Move the ``.app`` file to your ``Applications`` folder.

You can now UPPAAL app from the Applications folder.
macOS may put Uppaal into quarantine and suggest to “Move to Bin”.

1) Dismiss the popup with error message "UPPAAL" can't be opened because Apple cannot check it for malicious software or "UPPAAL" can't be opened because it was not downloaded from the App store by clicking OK.
2) Go to the Apple menu, select System Settings..., click Privacy & Security in the sidebar, and then scroll down to the Security section on the right.
3) Under Allow apps downloaded from, click the Open Anyway button just after "UPPAAL.app" was blocked from use because it is not from an identified developer, to allow the UPPAAL app to be executed.
4) Approve the application with your credentials in the next popup.
5) Start UPPAAL again (if not restarted automatically), and when the popup appears with the same error message as before, click Open.

Once successfully opened, we will now create a symbolic link to the UPPAAL engine:

.. code-block:: sh

  cd /usr/local/bin
  ln -s /Applications/<name of uppaal app file>/Contents/Resources/uppaal/bin/verifyta <short name>

``<short name>`` can be any name you like, but it will become the command that you (and, in fact,
*strategoutil*) call from a terminal. The suggestion is to always include the version number of the
downloaded UPPAAL Stratego. For example, if you downloaded ``uppaal-4.1.20-stratego-9-app.zip``,
then ``verifyta-stratego-9`` can be a good name, and the full command for the symbolic link becomes

.. code-block:: sh

  ln -s /Applications/uppaal-4.1.20-stratego-9.app/Contents/Resources/uppaal/bin/verifyta verifyta-stratego-9

.. note:: UPPAAL Stratego versions 7 and lower are not build for macOS.

Verify that the symbolic link is created correctly by typing

.. code-block:: sh

  <short name> -h

with the short name of the symbolic link, for example ``verifyta-stratego-9``. The command line
manual of UPPAAL Stratego should now be printed.

Finally, we check whether the symbolic link we created is recognized anywhere in the system. First,
navigate to another random folder, for example your home folder

.. code-block:: sh

  cd

and type

.. code-block:: sh

  <short name> -h

with the short name of the symbolic link, for example ``verifyta-stratego-9``. Again, the command line
manual of UPPAAL Stratego should now be printed. If so, we are ready to go. Otherwise, look at
:ref:`installation_problems`.

.. _installation_problems:

Problems with the installation
------------------------------

We will provide some known solutions to problems you might encounter setting up the *strategoutil*
package and UPPAAL Stratego.

Running verifyta command produces a ``No such file or directory`` error
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Older versions of UPPAAL Stratego (up to version 7) cannot properly cope with being installed in
``$HOME/.local/bin`` folder and having a symbolic link to it. You can solve this by replacing the
content of ``<uppaal stratego folder>/bin-Linux/verifyta`` to

.. code-block:: sh

  #!/usr/bin/env bash
  # Use this script when the native dynamic linker is incompatible
  SOURCE="${BASH_SOURCE[0]}"
  while [ -h "$SOURCE" ]; do
    HERE=$(cd -P $(dirname "$SOURCE") >/dev/null 2>&1 && pwd)
    SOURCE=$(readlink "$SOURCE")
    [[ "$SOURCE" != /* ]] && SOURCE="$HERE/$SOURCE"
  done
  HERE=$(cd -P $(dirname "$SOURCE") > /dev/null 2>&1 && pwd)
  export LD_LIBRARY_PATH="$HERE"
  exec -a verifyta "$HERE"/ld-linux.so "$HERE"/verifyta.bin "$@"


UPPAAL Stratego command cannot be found
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If *strategoutil* generates the runtime error ``Cannot find the supplied verifyta command:`` or a
terminal fails with ``command not found``, the symbolic link to UPPAAL Stratego is not in the path
variable.

We will first verify that the path variable is indeed the problem by opening a terminal and type

.. code-block:: sh

  echo $PATH

Check whether along the printed folders is the folder ``$HOME/.local/bin``, where ``$HOME`` is your
home folder (if you do not know this folder, type ``echo $HOME`` in the terminal). If this folder is
missing, both *strategoutil* and the terminal cannot find it.

.. note:: *strategoutil* has only access to commands through the path variable and not through any
  aliases defined in, for example, your ``.bashrc`` or ``.zshrc`` files. So it might be the case
  that UPPAAL Stratego is working when you call it with your terminal while *strategoutil* produces
  this runtime error.

You could temporarily solve the problem by running your script with *strategoutil* from the command
line with

.. code-block:: sh

  PATH=$HOME/.local/bin:$PATH python3 <name of script>

If you want to do a more thorough investigation, we will inspect the file `/etc/skel/.profile`, where
the user's bin folder is added to the path variable. Make sure that this file contains

.. code-block:: sh

  # set PATH so it includes user's private bin if it exists
  if [ -d "$HOME/.local/bin" ] ; then
      PATH="$HOME/.local/bin:$PATH"
  fi

If the file is missing this part, something might be wrong with your Linux OS, as this file comes with
the standard installation of Linux and will not be altered by most users. Therefore, instead of
adding the above lines to the file, it might be better to just reinstall your Linux OS.
