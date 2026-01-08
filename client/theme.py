"""Wordle TUI Theme - Premium color palette."""

COLORS = {
    # Wordle core colors
    "correct": "#6aaa64",
    "present": "#c9b458",
    "absent": "#787c7e",

    # UI colors
    "bg_primary": "#121213",
    "bg_secondary": "#1a1a1b",
    "border": "#3a3a3c",
    "border_active": "#565758",
    "border_bright": "#878a8c",

    # Text
    "text_primary": "#ffffff",
    "text_secondary": "#818384",
    "text_muted": "#565758",

    # Accent
    "accent": "#538d4e",
    "streak_fire": "#ff6b35",

    # Contribution graph
    "graph_level_0": "#161b22",
    "graph_level_1": "#0e4429",
    "graph_level_2": "#006d32",
    "graph_level_3": "#26a641",
    "graph_level_4": "#39d353",
    "graph_failed": "#da3633",
}


TCSS = """
$correct: #6aaa64;
$present: #c9b458;
$absent: #787c7e;
$bg-primary: #121213;
$bg-secondary: #1a1a1b;
$border: #3a3a3c;
$border-active: #565758;
$text-primary: #ffffff;
$text-secondary: #818384;

Screen {
    background: $bg-primary;
}

.title {
    text-align: center;
    text-style: bold;
    color: $text-primary;
    padding: 1;
}

.panel {
    border: round $border;
    background: $bg-secondary;
    padding: 1;
}

.stats-value {
    text-align: center;
    text-style: bold;
    color: $text-primary;
}

.stats-label {
    text-align: center;
    color: $text-secondary;
}
"""
