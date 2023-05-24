You can add custom theme in this directory. 
Keep in mind that you might need to tweak some of the tcl code to make the theme work.
The most compatible theme are the one made by rdbende - https://github.com/rdbende

To add custom theme the theme must have a `set_theme` proc (procedure - https://www.tcl.tk/man/tcl/TclCmd/proc.html) in the .tcl file. 
This `set_theme` procedure will be called when the theme is to be set (see example below). 

You might also need to isolate unused theme.
This can be done by moving it to the skip folder or by creating a new folder
in the themes folder and moving the theme (the whole directory of theme that you don't want to use) there.

------------------------------------------

Format:

/themes/<theme_name>/<theme_name>.tcl

Example:

/themes/sv/sv.tcl
/themes/test/test.tcl
/themes/azure/azure.tcl

...

Inside the .tcl file:

proc set_theme {param} {
    # set theme here
    if {$param ...} {
        # set theme here
    } else {
        # set theme here
    }
}

Called in ts_ttk:

root.tk.call("set_theme", theme) 

... 

You can see the customized sun valley theme in sv folder for more reference.

------------------------------------------


p.s. You can also customize the sun valley theme on your own if you want to