#!/bin/bash -e

pyuic5 testing_gui_main_window.ui -o testing_gui_main_window.py
pyuic5 testing_gui_testing_dialog.ui -o testing_gui_testing_dialog.py
echo "Done"
