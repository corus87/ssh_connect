import os
from prompt_toolkit.styles import Style

THEMES = {
    "solarized-dark": {
        "question":   "#b58900 bold",
        "cursor":     "#cb4b16 bold",
        "index":      "#93a1a1",
        "name":       "#268bd2 bold",
        "ip":         "#859900 bold",
        "sel_cursor": "#cb4b16 bold",
        "sel_index":  "#eee8d5 bold",
        "sel_name":   "#2aa198 bold",
        "sel_ip":     "#859900 bold",
    },
    "nord": {
        "question": "#88c0d0 bold",
        "cursor":   "#81a1c1 bold",
        "index":    "#4c566a",
        "name":     "#88c0d0 bold",
        "ip":       "#a3be8c bold",
        "sel_cursor": "#81a1c1 bold",
        "sel_index":  "#eceff4 bold",
        "sel_name":   "#8fbcbb bold",
        "sel_ip":     "#a3be8c bold",
    },
    "dracula": {
        "question": "#bd93f9 bold",
        "cursor":   "#ff79c6 bold",
        "index":    "#6272a4",
        "name":     "#bd93f9 bold",
        "ip":       "#50fa7b bold",
        "sel_cursor": "#ff79c6 bold",
        "sel_index":  "#f8f8f2 bold",
        "sel_name":   "#bd93f9 bold",
        "sel_ip":     "#50fa7b bold",
    },
    "gruvbox": {
        "question": "#fabd2f bold",
        "cursor":   "#fabd2f bold",
        "index":    "#665c54",
        "name":     "#fabd2f bold",
        "ip":       "#b8bb26 bold",
        "sel_cursor": "#fabd2f bold",
        "sel_index":  "#ebdbb2 bold",
        "sel_name":   "#d79921 bold",
        "sel_ip":     "#b8bb26 bold",
    },
    "neon": {
        "question": "#00ffff bold",
        "cursor":   "#ff0090 bold",
        "index":    "#551a8b",
        "name":     "#00ffff bold",
        "ip":       "#39ff14 bold",
        "sel_cursor": "#ff0090 bold",
        "sel_index":  "#fffb00 bold",
        "sel_name":   "#00b3ff bold",
        "sel_ip":     "#39ff14 bold",
    },
    "minimal": {
        "question": "#00afff bold",
        "cursor":   "#00afff bold",
        "index":    "#666666",
        "name":     "#00afff bold",
        "ip":       "#00d75f bold",
        "sel_cursor": "#00afff bold",
        "sel_index":  "#999999 bold",
        "sel_name":   "#5f87ff bold",
        "sel_ip":     "#00d75f bold",
    },
    "material": {
        "question": "#2196f3 bold",
        "cursor":   "#ff9800 bold",
        "index":    "#aaaaaa",
        "name":     "#5f87ff bold",
        "ip":       "#87af5f bold",
        "sel_cursor": "#ff9800 bold",
        "sel_index":  "#eeeeee bold",
        "sel_name":   "#03a9f4 bold",
        "sel_ip":     "#4caf50 bold",
    },
}

def get_style():
    theme = os.getenv("SSH_CONNECT_THEME", "material").lower()
    tokens = THEMES.get(theme, THEMES["material"])
    return Style.from_dict(tokens)
