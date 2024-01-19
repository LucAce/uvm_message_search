#!/usr/bin/env python3
#------------------------------------------------------------------------------
#  Copyright (c) 2023-2024 LucAce
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
#
#------------------------------------------------------------------------------
#  UVM Message Search Utility
#  File: uvm_message_search.py
#
#  Functional Description:
#
#      Search for SystemVerilog UVM style messages that contain one or more
#      strings.
#
#  Usage:
#
#      ./uvm_message_search.py [-h] [--debug]
#
#  Options:
#
#      -h, --help      Show the help message and exit
#      --debug         Enables debug output mode
#
#------------------------------------------------------------------------------

import sys
sys.dont_write_bytecode = True
import os
import argparse
import logging
import re
import traceback

import tkinter as tk
from tkinter import TclError, ttk
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import showerror


#------------------------------------------------------------------------------
# Global Attributes
#------------------------------------------------------------------------------

# Default Logging Configuration
logging.basicConfig(
    stream=sys.stdout, level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)

# Separation String
SEPERATION  = "..."

# UVM End of Test String
END_OF_TEST = "# --- UVM Report Summary ---"

# UVM Message Strings
UVM_MESSAGE = "# UVM_"
UVM_WARNING = "# UVM_WARNING"
UVM_ERROR   = "# UVM_ERROR"
UVM_FATAL   = "# UVM_FATAL"


#------------------------------------------------------------------------------
# SearchGUI
#------------------------------------------------------------------------------
class SearchGUI:

    #--------------------------------------------------------------------------
    # Function: __init__
    # SearchGUI object constructor.
    #
    # Parameters:
    # root - tk Root Object
    #--------------------------------------------------------------------------
    def __init__(self, root):
        self.root     = root
        self.elements = dict()

        self.file_name_entry       = tk.StringVar()
        self.search_string_entries = dict()
        self.search_frame_next     = int(0)

        self.search_inclusivity = tk.StringVar()
        self.search_inclusivity.set("Or")

        self.search_case_sensitive = tk.BooleanVar(value=False)

        self.search_type = tk.StringVar()
        self.search_type.set("text_search")

        self.search_context = tk.IntVar()
        self.search_context.set(0)

        self.search_always_show_errors   = tk.BooleanVar(value=True)
        self.search_always_show_warnings = tk.BooleanVar(value=True)
        self.search_show_line_numbers    = tk.BooleanVar(value=True)

        self.main_window(self.root, self.elements)

    #--------------------------------------------------------------------------
    # Function: main_window
    # Render the main window.
    #
    # Parameters:
    # parent   - tk parent object
    # elements - tk Widget elements
    #--------------------------------------------------------------------------
    def main_window(self, parent, elements):
        parent.title("UVM Message Search Utility")
        parent.minsize(700, 720)
        parent.geometry("700x720")

        parent = ttk.Frame(parent, padding="5 5 5 5")
        parent.grid(column=0, row=0, sticky=(tk.NS, tk.EW))
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        parent.pack(
            ipadx=10, ipady=0,
            fill=tk.BOTH, expand=True,
            anchor=tk.N
        )

        elements["FILE_SUBFRAME"]    = self.file_subframe(parent)
        elements["SEARCH_SUBFRAME"]  = self.search_subframe(parent)
        elements["RESULTS_SUBFRAME"] = self.results_subframe(parent)
        elements["SAVE_SUBFRAME"]    = self.save_subframe(parent)

    #--------------------------------------------------------------------------
    # Function: file_subframe
    # Render the file selection frame.
    #
    # Parameters:
    # parent - tk parent object
    #
    # Returns:
    # dict - Dictionary containing new widgets elements
    #--------------------------------------------------------------------------
    def file_subframe(self, parent):
        sfe = dict()

        # LabelFrame
        sfe["SUBFRAME"] = ttk.LabelFrame(
            parent,
            padding="5 1 10 5",
            borderwidth=1,
            relief=tk.SOLID,
            text=' Search In '
        )
        sfe["SUBFRAME"].pack(padx=5, pady=5, fill=tk.X, expand=False)

        # File Label
        sfe["LABEL"] = tk.Label(sfe["SUBFRAME"], text="File:")
        sfe["LABEL"].pack(ipadx=5, ipady=0, fill=tk.X, expand=False, side=tk.LEFT)

        # File Name Entry Box
        sfe["ENTRY"] = tk.Entry(sfe["SUBFRAME"], textvariable=self.file_name_entry)
        sfe["ENTRY"].focus()
        sfe["ENTRY"].pack(padx=5, ipady=2, fill=tk.X, expand=True, side=tk.LEFT)

        # File Open Dialog
        sfe["BUTTON"] = tk.Button(sfe["SUBFRAME"], text="...", command=self.open_file)
        sfe["BUTTON"].pack(ipadx=5, ipady=0, fill=tk.X, expand=False, side=tk.LEFT)

        return sfe

    #--------------------------------------------------------------------------
    # Function: search_subframe
    # Render the search string frame.
    #
    # Parameters:
    # parent - tk parent object
    #
    # Returns:
    # dict - Dictionary containing new widgets elements
    #--------------------------------------------------------------------------
    def search_subframe(self, parent):
        sfe = dict()

        # LabelFrame
        sfe["SUBFRAME"] = ttk.LabelFrame(
            parent,
            padding="5 1 5 5",
            borderwidth=1,
            relief=tk.SOLID,
            text=' Search '
        )
        sfe["SUBFRAME"].pack(padx=5, pady=5, fill=tk.X, expand=False)

        # Options Frame
        sfe["OPTIONS_FRAME"] = ttk.Frame(sfe["SUBFRAME"], padding="0 0 0 8", borderwidth=0)
        sfe["OPTIONS_FRAME"].pack(padx=5, pady=0, fill=tk.X, expand=False)

        # Text Search Mode Radio
        sfe["OPTIONS_TEXT_SEARCH"] = ttk.Radiobutton(
            sfe["OPTIONS_FRAME"],
            text='Text Search',
            value='text_search',
            variable=self.search_type,
            command=self.toggle_search_case_sensitivity
        )
        # Regex Search Mode Radio
        sfe["OPTIONS_REGEX_SEARCH"] = ttk.Radiobutton(
            sfe["OPTIONS_FRAME"],
            text='Regex Search',
            value='regex_search',
            variable=self.search_type,
            command=self.toggle_search_case_sensitivity
        )
        # Case Sensitive Mode Checkbutton
        sfe["OPTIONS_CASE_SENSITIVE"] = ttk.Checkbutton(
            sfe["OPTIONS_FRAME"],
            text='Case Sensitive',
            variable=self.search_case_sensitive
        )
        # Context Selection
        sfe["OPTIONS_CONTEXT_DIVIDER"] = ttk.Label(sfe["OPTIONS_FRAME"], text='|')
        sfe["OPTIONS_CONTEXT_LABEL"]   = ttk.Label(sfe["OPTIONS_FRAME"], text='Context Messages')

        sfe["OPTIONS_CONTEXT"] = ttk.Spinbox(
            sfe["OPTIONS_FRAME"],
            from_=0, to=10, width=3,
            textvariable=self.search_context
        )

        # Pack Radio Buttons and Checkbutton
        sfe["OPTIONS_TEXT_SEARCH"]    .pack(padx=5, pady=0, fill=tk.X, expand=False, side=tk.LEFT)
        sfe["OPTIONS_REGEX_SEARCH"]   .pack(padx=5, pady=0, fill=tk.X, expand=False, side=tk.LEFT)
        sfe["OPTIONS_CASE_SENSITIVE"] .pack(padx=5, pady=0, fill=tk.X, expand=False, side=tk.LEFT)
        sfe["OPTIONS_CONTEXT_DIVIDER"].pack(padx=5, pady=0, fill=tk.X, expand=False, side=tk.LEFT)
        sfe["OPTIONS_CONTEXT_LABEL"]  .pack(padx=5, pady=0, fill=tk.X, expand=False, side=tk.LEFT)
        sfe["OPTIONS_CONTEXT"]        .pack(padx=5, pady=0, fill=tk.X, expand=False, side=tk.LEFT)

        # Inner Frame (Grid Layout)
        sfe["SUBFRAME_INNER"] = ttk.Frame(sfe["SUBFRAME"], padding="0 0 0 0", borderwidth=0)
        sfe["SUBFRAME_INNER"].pack(padx=5, pady=0, fill=tk.X, expand=False)

        # Configure the columns
        sfe["SUBFRAME_INNER"].columnconfigure(0, weight=0)
        sfe["SUBFRAME_INNER"].columnconfigure(1, weight=1)
        sfe["SUBFRAME_INNER"].columnconfigure(2, weight=0)
        sfe["SUBFRAME_INNER"].columnconfigure(3, weight=0)

        # Search Label
        sfe["LABEL"] = tk.Label(sfe["SUBFRAME_INNER"], text="Search For:", anchor=tk.W, width=8)
        sfe["LABEL"].grid(column=0, row=0, ipadx=5, ipady=0, sticky=tk.W)

        # Search String Entry box
        key = self.search_frame_next
        self.search_frame_next += 1
        self.search_string_entries[key] = tk.StringVar()

        entry = tk.Entry(sfe["SUBFRAME_INNER"], textvariable=self.search_string_entries[key])
        entry.grid(column=1, row=0, padx=5, ipady=2, sticky=tk.EW)

        sfe["ENTRY"] = []
        sfe["ENTRY"].append(entry)

        # + Button
        sfe["BUTTON_ADD_SEARCH"] = tk.Button(
            sfe["SUBFRAME_INNER"],
            text="+",
            justify=tk.CENTER,
            width=1,
            command=self.search_additional_fields
        )
        sfe["BUTTON_ADD_SEARCH"].grid(column=2, row=0, ipadx=5, ipady=0, sticky=tk.E)

        # Search Button
        sfe["BUTTON_SEARCH"] = tk.Button(
            sfe["SUBFRAME_INNER"],
            text="Search",
            justify=tk.CENTER,
            padx=10,
            width=6,
            command=self.search_file
        )
        sfe["BUTTON_SEARCH"].grid(column=3, row=0, ipadx=5, ipady=0, sticky=tk.E)
        self.root.bind('<Return>', lambda event=None: sfe["BUTTON_SEARCH"].invoke())

        # Initialize additional search sub-frames
        sfe["SEARCH_OR"] = dict()

        return sfe

    #--------------------------------------------------------------------------
    # Function: search_additional_fields
    # Add a search entry frame.
    #--------------------------------------------------------------------------
    def search_additional_fields(self):
        key = self.search_frame_next
        self.search_frame_next += 1

        logging.debug("Adding Search Field: " + str(key))

        sfe = self.elements["SEARCH_SUBFRAME"]["SEARCH_OR"]
        sfe[key] = dict()

        # AND/OR Button
        sfe[key]["BUTTON_AND_OR"] = tk.Button(
            self.elements["SEARCH_SUBFRAME"]["SUBFRAME_INNER"],
            textvariable=self.search_inclusivity,
            justify=tk.CENTER,
            width=2,
            command=self.toggle_search_inclusivity
        )
        sfe[key]["BUTTON_AND_OR"].grid(column=0, row=key, ipadx=5, ipady=0, sticky=tk.E)

        # Search Entry Box
        self.search_string_entries[key] = tk.StringVar()

        sfe[key]["ENTRY"] = tk.Entry(
            self.elements["SEARCH_SUBFRAME"]["SUBFRAME_INNER"],
            textvariable=self.search_string_entries[key]
        )
        sfe[key]["ENTRY"].grid(column=1, row=key, padx=5, ipady=2, sticky=tk.EW)

        # - Button
        sfe[key]["BUTTON"] = tk.Button(
            self.elements["SEARCH_SUBFRAME"]["SUBFRAME_INNER"],
            text="-",
            justify=tk.CENTER,
            width=1,
            command=lambda: self.search_fewer_fields(key)
        )
        sfe[key]["BUTTON"].grid(column=2, row=key, ipadx=5, ipady=0, sticky=tk.E)

        # Spacing Label
        sfe[key]["SPACING"] = tk.Label(
            self.elements["SEARCH_SUBFRAME"]["SUBFRAME_INNER"],
            anchor=tk.E,
            padx=0
        )
        sfe[key]["SPACING"].grid(column=3, row=key, ipadx=5, ipady=0, sticky=tk.E)

        # Disable the "+" button when there are 9 additional search entries (for total of 10)
        if len(sfe) >= 9:
            self.elements["SEARCH_SUBFRAME"]["BUTTON_ADD_SEARCH"].configure(state='disabled')

    #--------------------------------------------------------------------------
    # Function: search_fewer_fields
    # Remove a search entry.
    #
    # Parameters:
    # key - tk search element to remove
    #--------------------------------------------------------------------------
    def search_fewer_fields(self, key):
        logging.debug("Deleting Search Field: " + str(key))

        sfe = self.elements["SEARCH_SUBFRAME"]["SEARCH_OR"]

        sfe[key]["BUTTON_AND_OR"].destroy()
        sfe[key]["ENTRY"].destroy()
        sfe[key]["BUTTON"].destroy()
        sfe[key]["SPACING"].destroy()
        del sfe[key]
        del self.search_string_entries[key]

        # Re-enable the "+" button if there are less than 9 additional search entries
        if len(sfe) < 9:
            self.elements["SEARCH_SUBFRAME"]["BUTTON_ADD_SEARCH"].configure(state='normal')

    #--------------------------------------------------------------------------
    # Function: toggle_search_case_sensitivity
    # Disable case sensivity GUI element when the search type is regex.
    #--------------------------------------------------------------------------
    def toggle_search_case_sensitivity(self):
        if self.search_type.get() == "text_search":
            self.elements["SEARCH_SUBFRAME"]["OPTIONS_CASE_SENSITIVE"].configure(state='enabled')
        else:
            self.elements["SEARCH_SUBFRAME"]["OPTIONS_CASE_SENSITIVE"].configure(state='disabled')

    #--------------------------------------------------------------------------
    # Function: toggle_search_inclusivity
    # Toggle AND/OR search mode.
    #--------------------------------------------------------------------------
    def toggle_search_inclusivity(self):
        if self.search_inclusivity.get() == "Or":
            self.search_inclusivity.set("And")
        else:
            self.search_inclusivity.set("Or")

    #--------------------------------------------------------------------------
    # Function: results_subframe
    # Render the results frame.
    #
    # Parameters:
    # parent - tk parent object
    #
    # Returns:
    # dict - Dictionary containing new widgets elements
    #--------------------------------------------------------------------------
    def results_subframe(self, parent):
        sfe = dict()

        # LabelFrame
        sfe["SUBFRAME"] = ttk.LabelFrame(
            parent,
            padding="5 1 5 1",
            borderwidth=1,
            relief=tk.SOLID,
            text=' Search Results '
        )
        sfe["SUBFRAME"].pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        # Options Frame
        sfe["OPTIONS_FRAME"] = ttk.Frame(sfe["SUBFRAME"], padding="0 0 0 5", borderwidth=0)
        sfe["OPTIONS_FRAME"].pack(padx=5, pady=0, fill=tk.X, expand=False)

        # Always Show Errors Checkbutton
        sfe["OPTIONS_ALWAYS_SHOW_ERROR"] = ttk.Checkbutton(
            sfe["OPTIONS_FRAME"],
            text='Always Show Errors',
            variable=self.search_always_show_errors
        )
        # Always Show Warnings Checkbutton
        sfe["OPTIONS_ALWAYS_SHOW_WARNINGS"] = ttk.Checkbutton(
            sfe["OPTIONS_FRAME"],
            text='Always Show Warnings',
            variable=self.search_always_show_warnings
        )
        # Show Line Numbers Checkbutton
        sfe["OPTIONS_SHOW_LINE_NUMBERS"] = ttk.Checkbutton(
            sfe["OPTIONS_FRAME"],
            text='Show Line Numbers',
            variable=self.search_show_line_numbers
        )
        sfe["OPTIONS_ALWAYS_SHOW_ERROR"]   .pack(padx=5, pady=0, fill=tk.X, expand=False, side=tk.LEFT)
        sfe["OPTIONS_ALWAYS_SHOW_WARNINGS"].pack(padx=5, pady=0, fill=tk.X, expand=False, side=tk.LEFT)
        sfe["OPTIONS_SHOW_LINE_NUMBERS"]   .pack(padx=5, pady=0, fill=tk.X, expand=False, side=tk.LEFT)

        # Scrolling Text
        sfe["SCROLLED_TEXT_ENTRY"] = ScrolledText(sfe["SUBFRAME"], state='disabled', height=3)
        sfe["SCROLLED_TEXT_ENTRY"].pack(padx=5, pady=(0,10), ipady=0, fill=tk.BOTH, expand=True)
        sfe["SCROLLED_TEXT_ENTRY"].configure(wrap='none')

        return sfe

    #--------------------------------------------------------------------------
    # Function: save_subframe
    # Render the save/quit frame.
    #
    # Parameters:
    # parent - tk parent object
    #
    # Returns:
    # dict - Dictionary containing new widgets elements
    #--------------------------------------------------------------------------
    def save_subframe(self, parent):
        sfe = dict()

        # Frame
        sfe["SUBFRAME"] = ttk.Frame(parent, padding="5 1 5 5")
        sfe["SUBFRAME"].pack(padx=5, pady=5, fill=tk.X, expand=False)

        # Quit Button
        sfe["BUTTON_QUIT"] = tk.Button(
            sfe["SUBFRAME"],
            text="Quit",
            width=8,
            command=lambda root=self.root:quit(self.root)
        )
        sfe["BUTTON_QUIT"].pack(padx=0, ipady=0, fill=tk.X, expand=False, side=tk.RIGHT)

        # Save Button
        sfe["BUTTON_SAVE"] = tk.Button(
            sfe["SUBFRAME"],
            text="Save",
            width=8,
            command=self.save_file
        )
        sfe["BUTTON_SAVE"].pack(padx=5, ipady=0, fill=tk.X, expand=False, side=tk.RIGHT)

        return sfe

    #--------------------------------------------------------------------------
    # Function: open_file
    # Open the file to be searched.
    #--------------------------------------------------------------------------
    def open_file(self):
        # Get file using the open file dialog
        file_name = askopenfilename(
            title="Select File To Search",
            filetypes=(
                ("All Files", "*"),
                ("Log Files", "*.log"),
                ("Text Files", "*.txt"),
                ("Transcript Files", "*.tran")),
        )

        # Return if selection cancelled (Tuple is empty)
        if len(file_name) == 0:
            return

        file_name = str(file_name)
        logging.debug("File Selected: " + file_name)

        self.elements["RESULTS_SUBFRAME"]["SCROLLED_TEXT_ENTRY"].configure(state='normal')
        self.elements["RESULTS_SUBFRAME"]["SCROLLED_TEXT_ENTRY"].delete('1.0', tk.END)
        self.elements["RESULTS_SUBFRAME"]["SCROLLED_TEXT_ENTRY"].configure(state='disabled')

        self.file_name_entry.set(file_name)

    #--------------------------------------------------------------------------
    # Function: search_file
    # Search the file.
    #--------------------------------------------------------------------------
    def search_file(self):
        search_strings = []
        search_options = dict()

        self.elements["RESULTS_SUBFRAME"]["SCROLLED_TEXT_ENTRY"].configure(state='normal')
        self.elements["RESULTS_SUBFRAME"]["SCROLLED_TEXT_ENTRY"].delete('1.0', tk.END)
        self.elements["RESULTS_SUBFRAME"]["SCROLLED_TEXT_ENTRY"].configure(state='disabled')

        file_name = self.file_name_entry.get()

        if not os.path.exists(str(file_name)):
            logging.debug("File Does Not Exist: \"" + str(file_name) + "\"")
            showerror("Error", "Selected File Does Not Exist")
            return

        # Create Options Dictionary
        if self.search_case_sensitive.get():
            search_options["SEARCH_CASE_SENSITIVE"] = True
        else:
            search_options["SEARCH_CASE_SENSITIVE"] = False

        if self.search_inclusivity.get() == "And":
            search_options["SEARCH_EXCLUSIVE"] = True
        else:
            search_options["SEARCH_EXCLUSIVE"] = False

        if self.search_always_show_errors.get():
            search_options["SHOW_ERRORS"] = True
        else:
            search_options["SHOW_ERRORS"] = False

        if self.search_always_show_warnings.get():
            search_options["SHOW_WARNINGS"] = True
        else:
            search_options["SHOW_WARNINGS"] = False

        if self.search_show_line_numbers.get():
            search_options["SHOW_LINE_NUMBERS"] = True
        else:
            search_options["SHOW_LINE_NUMBERS"] = False

        if self.search_type.get() == "regex_search":
            search_options["SEARCH_REGEX"]          = True
            search_options["SEARCH_CASE_SENSITIVE"] = True
        else:
            search_options["SEARCH_REGEX"]          = False

        search_options["SEARCH_CONTEXT"] = int(self.search_context.get())

        for key,value in self.search_string_entries.items():
            if value.get() == "":
                continue
            logging.debug("Searching For: " + value.get())
            search_strings.append(str(value.get()))

        search_results = SearchFile.search(str(file_name), search_strings, search_options)

        self.elements["RESULTS_SUBFRAME"]["SCROLLED_TEXT_ENTRY"].configure(state='normal')
        self.elements["RESULTS_SUBFRAME"]["SCROLLED_TEXT_ENTRY"].delete('1.0', tk.END)

        for line in search_results:
            self.elements["RESULTS_SUBFRAME"]["SCROLLED_TEXT_ENTRY"].insert(tk.INSERT, line)

        self.elements["RESULTS_SUBFRAME"]["SCROLLED_TEXT_ENTRY"].configure(state='disabled')

    #--------------------------------------------------------------------------
    # Function: save_file
    # Save the search results.
    #--------------------------------------------------------------------------
    def save_file(self):
        # Get the file to save to using the save dialog
        save_file_name = asksaveasfilename(
            title="Save Search Results",
            filetypes=(
                ("All Files", "*"),
                ("Log Files", "*.log"),
                ("Text Files", "*.txt"),
                ("Transcript Files", "*.tran")),
        )

        # Return if selection cancelled (Tuple is empty)
        if len(save_file_name) == 0:
            return

        save_file_name = str(save_file_name)
        logging.debug("Saving File: " + save_file_name)

        # Open file and write contents
        with open(save_file_name, 'w') as fh:
            fh.write(self.elements["RESULTS_SUBFRAME"]["SCROLLED_TEXT_ENTRY"].get(1.0, tk.END))


#------------------------------------------------------------------------------
# SearchFile
#------------------------------------------------------------------------------
class SearchFile:

    #--------------------------------------------------------------------------
    # Function: search
    # Search the file for the strings.
    #
    # Parameters:
    # file_name      - File to search
    # search_strings - List of strings to search for
    # search_options - Dictionary of option strings
    #
    # Returns:
    # list - Matched message strings
    #--------------------------------------------------------------------------
    @staticmethod
    def search(
        file_name,
        search_strings,
        search_options=dict()
    ):
        messages    = []
        buffer      = []
        file        = []
        text        = []
        matches     = dict()
        match       = False
        last        = False
        context     = 0
        line_number = 0

        # Local Matching Strings
        end_of_test_string = END_OF_TEST
        uvm_message_string = UVM_MESSAGE
        uvm_warning_string = UVM_WARNING
        uvm_error_string   = UVM_ERROR
        uvm_fatal_string   = UVM_FATAL

        # Options
        search_regex          = False
        search_case_sensitive = False
        search_exclusive      = False
        always_show_errors    = False
        always_show_warnings  = False
        show_line_numbers     = False
        search_context        = 0

        # Decode search options
        if "SEARCH_CASE_SENSITIVE" in search_options.keys() and \
            search_options["SEARCH_CASE_SENSITIVE"] == True:
            search_case_sensitive = True

        if "SEARCH_EXCLUSIVE" in search_options.keys() and \
            search_options["SEARCH_EXCLUSIVE"] == True:
            search_exclusive = True

        if "SHOW_ERRORS" in search_options.keys() and \
            search_options["SHOW_ERRORS"] == True:
            always_show_errors = True

        if "SHOW_WARNINGS" in search_options.keys() and \
            search_options["SHOW_WARNINGS"] == True:
            always_show_warnings = True

        if "SHOW_LINE_NUMBERS" in search_options.keys() and \
            search_options["SHOW_LINE_NUMBERS"] == True:
            show_line_numbers = True

        if "SEARCH_REGEX" in search_options.keys() and \
            search_options["SEARCH_REGEX"] == True:
            search_regex          = True
            search_case_sensitive = True

        if "SEARCH_CONTEXT" in search_options.keys():
            search_context = int(search_options["SEARCH_CONTEXT"])

        logging.debug("Searching File: "              + file_name)
        logging.debug("Search Regex: "                + str(search_regex))
        logging.debug("Search Case Sensitive: "       + str(search_case_sensitive))
        logging.debug("Search Exclusive: "            + str(search_exclusive))
        logging.debug("Search Always Show Errors: "   + str(always_show_errors))
        logging.debug("Search Always Show Warnings: " + str(always_show_warnings))
        logging.debug("Search Show Line Numbers: "    + str(show_line_numbers))
        logging.debug("Search Context Lines: "        + str(search_context))

        for search_string in search_strings:
            logging.debug("Search For: " + str(search_string))

        # Open file and read contents
        file_lines = 0
        with open(file_name, 'r') as fh:
            file       = fh.readlines()
            file_lines = len(file)

        # Get the width of the number of lines
        line_number_width = len(str(file_lines))

        # Store the number of search strings
        search_strings_count = len(search_strings)

        # Convert to lower case if enabled
        if not search_case_sensitive:
            end_of_test_string = end_of_test_string.lower()
            uvm_message_string = uvm_message_string.lower()
            uvm_warning_string = uvm_warning_string.lower()
            uvm_error_string   = uvm_error_string.lower()
            uvm_fatal_string   = uvm_fatal_string.lower()

            for i in range(0, len(search_strings)):
                search_strings[i] = search_strings[i].lower()

        # Search the file's contents
        for line in file:
            line_number += 1

            # Remove trailing characters
            line = line.rstrip()

            # Remove character escapes
            line = re.sub(r"\x1b(?:\[.*?m)", "", line)

            # Create a copy of the line for potential modifications
            fline = str(line)

            # Convert to lower case if enabled
            if not search_case_sensitive:
                fline = fline.lower()

            # Message header, end of test message, or end of file found
            if fline.startswith(uvm_message_string) or \
               end_of_test_string in fline:

                # Add buffer to the message list
                if len(buffer) > 0:
                    messages.append(buffer.copy())

                # Clear the buffer
                buffer = []

                # Maintain the list of messages to the size of the context + 1
                messages = messages[((search_context+1) * -1):]

                # If a match was found, print the message and any context
                if match or context > 0:
                    # Add visual cue that there is a break
                    if not last:
                        last = False
                        text.append(SEPERATION + "\n")

                    # Print all the stored messages
                    for message in messages:
                        for (location, entry) in message:
                            if show_line_numbers:
                                text.append(str(location) + ": " + entry + "\n")
                            else:
                                text.append(entry + "\n")

                    messages = []
                    last = True
                else:
                    last = False

                # Decrement a context match
                if context > 0:
                    context -= 1

                # Reset context match on match
                if match:
                    context = search_context

                # Reset match flag
                match = False

            # Return if the end of the test message is seen
            if end_of_test_string in fline:
                file     = []
                messages = []
                buffer   = []
                return text

            # Store the line and line number to the buffer
            line_number_formated = '{number:<{number_size}}'.format(
                number=line_number, number_size=line_number_width
            )
            buffer.append((line_number_formated, line))

            # Print Fatal messages, always printed
            if fline.startswith(uvm_fatal_string):
                match = True

            # Print Error messages, print if enabled
            if (always_show_errors is True) and fline.startswith(uvm_error_string):
                match = True

            # Print Warning messages, print if enabled
            if (always_show_warnings is True) and fline.startswith(uvm_warning_string):
                match = True

            # Look for a match in the current line
            if search_exclusive:
                for search_string in search_strings:
                    if search_regex:
                        if re.search(search_string, line):
                            matches[search_string] = 1
                    else:
                        if search_string in fline:
                            matches[search_string] = 1

                if len(matches) == search_strings_count and search_strings_count > 0:
                    match = True
            else:
                for search_string in search_strings:
                    if search_regex:
                        if re.search(search_string, line):
                            match = True
                    else:
                        if search_string in fline:
                            match = True

        # Print any remaining matches
        if match or context > 0:
            # Add visual cue that there is a break
            if not last:
                last = False
                text.append(SEPERATION + "\n")

            # Remove the oldest message if it wasn't printed as it
            # will be an extra message
            if len(messages) > 0:
                messages.pop(0)

            messages = messages[((search_context+1) * -1):]

            # Print all the remaining stored messages
            for message in messages:
                for (location, entry) in message:
                    if show_line_numbers:
                        text.append(str(location) + ": " + entry + "\n")
                    else:
                        text.append(entry + "\n")

            # Print the remaining buffer
            for (location, entry) in buffer:
                if show_line_numbers:
                    text.append(str(location) + ": " + entry + "\n")
                else:
                    text.append(entry + "\n")

        # Search complete
        file     = []
        messages = []
        buffer   = []

        return text


#------------------------------------------------------------------------------
# main
#------------------------------------------------------------------------------
def main():

    #--------------------------------------------------------------------------
    # Gather, Parse, and Verify Command Line Switches
    #--------------------------------------------------------------------------

    # Create Option Parser
    parser = argparse.ArgumentParser(description='UVM Message Search Utility')

    # Debug Output Mode
    parser.add_argument(
        '--debug', dest="debug", action='store_true', default=False,
        required=False, help='Enables debug output mode'
    )

    # Parse command line
    args = parser.parse_args()

    #--------------------------------------------------------------------------
    # Configure Logging
    #--------------------------------------------------------------------------

    # Debug script mode
    if (args.debug == True):
        logging.basicConfig(
            force=True, stream=sys.stdout, level=logging.DEBUG,
            format='%(levelname)s: %(message)s'
        )
    # Normal mode
    else:
        logging.disable(logging.INFO)

    #--------------------------------------------------------------------------
    # Execute
    #--------------------------------------------------------------------------
    root = tk.Tk()
    SearchGUI(root)
    root.mainloop()


#------------------------------------------------------------------------------
# Call main()
#------------------------------------------------------------------------------
if __name__ == '__main__':

    try:
        main()

    # Ctrl-C
    except KeyboardInterrupt as e:
        logging.error("Break Requested ... exiting")
        sys.exit(1)

    # System Exit
    except SystemExit as e:
        sys.exit(0)

    # Other Exit
    except Exception as e:
        traceback.print_exc()
        logging.error("Unexpected exception: %s" % str(e))
        sys.exit(1)
