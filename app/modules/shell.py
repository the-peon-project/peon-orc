#!/usr/bin/python3
# FUNCTION: Run bash commands
import subprocess
import logging

def execute_shell( cmd_as_string, show_console=False ):
    logging.info('[execute_shell] - {0}'.format(cmd_as_string))
    # Run the shell command and return the result in human readable
    response = subprocess.check_output(cmd_as_string, shell=True).decode("utf-8")
    # Convert the result into a list (based on the newline character)
    output = response.split("\n")
    # If the final line was a blank, then remove it from the list.
    if output[-1] == '':
        del output[-1]
    if show_console:
        print("--------[SHELL]--------\n")
        print("> " + cmd_as_string)
        print (response)
        print("-----------------------")
    logging.debug('[execute_shell] - response: {0}'.format(output))
    return output