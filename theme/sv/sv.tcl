package require Tk 8.6

if {[tk windowingsystem] == "win32"} {
  set static ""
} else {
  set static " static"
}

font create SunValleyCaptionFont -family "Segoe UI Variable$static Small" -size -11
font create SunValleyBodyFont -family "Segoe UI Variable$static Text" -size -12
font create SunValleyBodyStrongFont -family "Segoe UI Variable$static Text Semibold" -size -12
font create SunValleyBodyLargeFont -family "Segoe UI Variable$static Text" -size -14
font create SunValleySubtitleFont -family "Segoe UI Variable$static Display Semibold" -size -16
font create SunValleyTitleFont -family "Segoe UI Variable$static Display Semibold" -size -24
font create SunValleyTitleLargeFont -family "Segoe UI Variable$static Display Semibold" -size -34
font create SunValleyDisplayFont -family "Segoe UI Variable$static Display Semibold" -size -48

proc config_input_font {w} {
  if {[ttk::style theme use] in [list "sun-valley-dark" "sun-valley-light"]} {
    $w configure -font SunValleyBodyFont
  }
}

proc config_menus {w} {
  if {[tk windowingsystem] != "aqua"} {
    set theme [ttk::style theme use]
    if {$theme == "sun-valley-dark"} {
      $w configure \
        -relief solid \
        -borderwidth 1 \
        -activeborderwidth 0 \
        -background "#202020" \
        -activebackground "#434343" \
        -activeforeground "#fafafa" \
        -selectcolor "#fafafa"
    } elseif {$theme == "sun-valley-light"} {
      $w configure \
        -relief solid \
        -borderwidth 1 \
        -activeborderwidth 0 \
        -background "#ebebeb" \
        -activebackground "#c4c4c4" \
        -activeforeground "#1c1c1c" \
        -selectcolor "#1c1c1c"
    }

    if {[[winfo toplevel $w] cget -menu] != $w} {
      if {$theme == "sun-valley-dark"} {
        $w configure -borderwidth 0 -background $ttk::theme::sv_dark::theme_colors(-bg)
      } elseif {$theme == "sun-valley-light"} {
        $w configure -borderwidth 0 -background $ttk::theme::sv_light::theme_colors(-bg)
      }
    }
  }
}

bind TEntry <<ThemeChanged>> {config_input_font %W}
bind TCombobox <<ThemeChanged>> {config_input_font %W}
bind TSpinbox <<ThemeChanged>> {config_input_font %W}
bind Menu <<ThemeChanged>> {config_menus %W}

source [file join [file dirname [info script]] resource light.tcl]
source [file join [file dirname [info script]] resource dark.tcl]


proc set_theme {mode} {
  if {$mode == "sv-dark"} {
    ttk::style theme use "sun-valley-dark"

    ttk::style configure . \
      -background $ttk::theme::sv_dark::theme_colors(-bg) \
      -foreground $ttk::theme::sv_dark::theme_colors(-fg) \
      -troughcolor $ttk::theme::sv_dark::theme_colors(-bg) \
      -focuscolor $ttk::theme::sv_dark::theme_colors(-selbg) \
      -selectbackground $ttk::theme::sv_dark::theme_colors(-selbg) \
      -selectforeground $ttk::theme::sv_dark::theme_colors(-selfg) \
      -insertwidth 1 \
      -insertcolor $ttk::theme::sv_dark::theme_colors(-fg) \
      -fieldbackground $ttk::theme::sv_dark::theme_colors(-bg) \
      -borderwidth 0 \
      -relief flat

    tk_setPalette \
      background $ttk::theme::sv_dark::theme_colors(-bg) \
      foreground $ttk::theme::sv_dark::theme_colors(-fg) \
      highlightColor $ttk::theme::sv_dark::theme_colors(-selbg) \
      selectBackground $ttk::theme::sv_dark::theme_colors(-selbg) \
      selectForeground $ttk::theme::sv_dark::theme_colors(-selfg) \
      activeBackground $ttk::theme::sv_dark::theme_colors(-selbg) \
      activeForeground $ttk::theme::sv_dark::theme_colors(-selfg)

    ttk::style map . -foreground [list disabled $ttk::theme::sv_dark::theme_colors(-disfg)]

    option add *tearOff 0

  } elseif {$mode == "sv-light"} {
    ttk::style theme use "sun-valley-light"

    ttk::style configure . \
      -background $ttk::theme::sv_light::theme_colors(-bg) \
      -foreground $ttk::theme::sv_light::theme_colors(-fg) \
      -troughcolor $ttk::theme::sv_light::theme_colors(-bg) \
      -focuscolor $ttk::theme::sv_light::theme_colors(-selbg) \
      -selectbackground $ttk::theme::sv_light::theme_colors(-selbg) \
      -selectforeground $ttk::theme::sv_light::theme_colors(-selfg) \
      -insertwidth 1 \
      -insertcolor $ttk::theme::sv_light::theme_colors(-fg) \
      -fieldbackground $ttk::theme::sv_light::theme_colors(-bg) \
      -borderwidth 0 \
      -relief flat

    tk_setPalette \
      background $ttk::theme::sv_light::theme_colors(-bg) \
      foreground $ttk::theme::sv_light::theme_colors(-fg) \
      highlightColor $ttk::theme::sv_light::theme_colors(-selbg) \
      selectBackground $ttk::theme::sv_light::theme_colors(-selbg) \
      selectForeground $ttk::theme::sv_light::theme_colors(-selfg) \
      activeBackground $ttk::theme::sv_light::theme_colors(-selbg) \
      activeForeground $ttk::theme::sv_light::theme_colors(-selfg)

    ttk::style map . -foreground [list disabled $ttk::theme::sv_light::theme_colors(-disfg)]

    option add *tearOff 0
  }
}
