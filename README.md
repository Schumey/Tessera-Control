# Tessera Control

[Deutsch](README.de.md)

Home Assistant configuration that turns a [Tessera](https://github.com/MaxGramser/homeassistant_espscreen) touch
screen into a status display that runs by itself:

- **Page rotation.** The screen moves through its pages at an interval you set.
- **Pages by situation.** Which pages are in the rotation depends on what is going on: the home page always, the
  PC page while the PC is on, the printer page while it prints. A page that joins shows at once.
- **Brightness by situation.** One level by day, one in the evening, one when nobody is home or the room is dark
  (for example 100 %, 60 % and 20 %), each set with a slider; off while you sleep.
- **Buttons on a dashboard** that jump to a page and pause the rotation for a few minutes.

Everything is plain Home Assistant: a package with helpers, two automations, a script and a dashboard card. Nothing is
installed on the screen, and nothing needs a firmware build.

## How it works

Tessera's firmware gives Home Assistant an action per screen, `esphome.<node>_show_page`, and entities such as
`switch.<screen>_back_to_page_1`, `number.<screen>_normal_brightness` and `button.<screen>_wake`. This configuration
only uses those.

| File | What |
|---|---|
| [`packages/tessera_control.yaml`](packages/tessera_control.yaml) | The helpers: the page list (a template sensor), the rotation timer, the interval, the current page, the rotation switch, the three brightness levels. |
| [`automations/tessera_page_rotation.yaml`](automations/tessera_page_rotation.yaml) | Shows the next page when the timer ends, and reacts when the page list changes. |
| [`automations/tessera_brightness.yaml`](automations/tessera_brightness.yaml) | Sets the brightness from presence, sleep, the sun and the room's lights, using the three levels. |
| [`scripts/tessera_show_page.yaml`](scripts/tessera_show_page.yaml) | Shows one page and pauses the rotation. For dashboard buttons. |
| [`dashboards/tessera_buttons.yaml`](dashboards/tessera_buttons.yaml) | A card with a button per page, the rotation switch and sliders for the brightness levels. |

## Placeholders

The files are a template: replace every `YOUR_...` with your own entity before you use them.

| Placeholder | What to put there | Where to find it |
|---|---|---|
| `YOUR_NODE` | The screen's ESPHome node name, with `_` for `-` (`dsp-desktop` → `dsp_desktop`) | Tools → Actions: search "show_page" |
| `YOUR_SCREEN` | The prefix of the screen's entities (`switch.moin_back_to_page_1` → `moin`). Often not the same as the node name. | Settings → Devices → your screen |
| `binary_sensor.YOUR_SLEEP` | On while you sleep | Your own sensor or helper |
| `input_boolean.YOUR_PRESENCE` | On while someone is home | Your own sensor or helper |
| `light.YOUR_ROOM_LIGHTS` | The light or light group that makes the room "lit" | Settings → Entities |
| `binary_sensor.YOUR_PC` | On while the PC is on (the Ping integration, for example) | Settings → Entities |
| `sensor.YOUR_PRINTER_STATE` | The printer's state, `printing` while it prints | Settings → Entities |

Page numbers start at 1. The examples use 1 for home, 2 for the PC and 3 for the printer: change them in the page list
and on the buttons.

## Set up

1. Make sure Home Assistant loads packages: `configuration.yaml` has
   `homeassistant: packages: !include_dir_named packages`.
2. Copy `packages/tessera_control.yaml` to `/config/packages/`, replace its placeholders, check the configuration
   (Tools → YAML → Check configuration) and restart Home Assistant.
3. Set **Tessera rotation interval** to the seconds you want between pages (it starts at 10 the first time), and
   **Tessera brightness day**, **evening** and **dim** to the levels you want (they start at 5 % the first time).
4. Create the script: Settings → Automations & scenes → Scripts → Create script → ⋮ → Edit in YAML, paste
   `scripts/tessera_show_page.yaml` with your placeholders, save it as `script.tessera_show_page`.
5. Create both automations the same way from `automations/`.
6. Turn off any automation of your own that switched pages or set the brightness of this screen.
7. Add the card from `dashboards/tessera_buttons.yaml` to a dashboard (Add card → Manual).
8. Turn on **Tessera rotation**.

## Adding a page

Add one line to the template of **Tessera page list** in the package, with the condition and the page number:

```jinja
{% if is_state('media_player.living_room', 'playing') %}{% set p = p + [4] %}{% endif %}
```

The automations need no change. Add a button to the card if you like.

## Limits

- **Home Assistant does not see touches.** The rotation goes on while someone swipes through the pages. Made for a
  screen that is looked at, not used.
- **Home Assistant does not know the page on the glass,** only the one it showed last.
- **One screen.** For a second screen, copy the files and give the helpers other names.
- The action and entity names come from Tessera's firmware, not from its documented plugin API: a Tessera update may
  rename them.

## Licence

MIT, see [LICENSE](LICENSE).
