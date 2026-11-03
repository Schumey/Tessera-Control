# Tessera Control

[Deutsch](README.de.md)

A Home Assistant integration that turns a [Tessera](https://github.com/MaxGramser/homeassistant_espscreen) touch
screen into a status display that runs by itself:

- **Page rotation.** The screen moves through its pages at an interval you set.
- **Pages by situation.** Each page is in the rotation always, or only while an entity has certain states: the PC
  page while the PC is on, the printer page while it prints. A page that joins shows at once.
- **Brightness by situation.** Three brightness levels, each set with a slider, and for every situation (day,
  evening, dark room, nobody home) the level it gets; the screen goes off while you sleep.
- **A button per page** for dashboards and scripts: it shows the page and pauses the rotation for a few minutes.

Nothing is installed on the screen, and nothing needs a firmware build: the integration uses the action and entities
Tessera's firmware already gives Home Assistant.

## Install

With [HACS](https://hacs.xyz):

1. HACS → ⋮ → **Custom repositories**: add `https://github.com/Schumey/Tessera-Control`, type **Integration**.
2. Search for **Tessera Control** in HACS and download it.
3. Restart Home Assistant.

By hand: copy `custom_components/tessera_control` into your `config/custom_components/` and restart.

Home Assistant 2026.10 or later.

## Set up

1. Settings → Devices & services → **Add integration** → **Tessera Control**, and choose the screen. It must be
   online.
2. On the integration's entry, **Add page** once for every page you want in the rotation:
   - **Name**: shown on the page's button.
   - **Page number**: the page's number on the screen; the first page is 1.
   - **In the rotation**: *Always*, or *When an entity is in one of these states* with the entity and its states
     (for a printer: `printing`, `paused`).
3. **Configure** sets what the brightness follows: a sleep entity, a presence entity, the room's lights (all
   optional), and which level each situation gets.
4. Turn on **Page rotation** and **Automatic brightness** on the screen's device page.

A page can be changed or deleted on the entry at any time.

## What you get

All on the screen's own device page:

| Entity | What |
|---|---|
| Page rotation (switch) | Rotation on or off. Off gives the screen its own "Back to page 1" again, unless *Keep "Back to page 1" off* is set. |
| Automatic brightness (switch) | Brightness by situation on or off. Off keeps the last brightness. |
| Rotation interval (number) | Seconds between two pages, 10 to 600. |
| Brightness level 1, 2, 3 (numbers) | The three levels, 5 to 100 %, as sliders. A new level applies at once. |
| Pages in rotation (sensor) | The pages in the rotation now, such as `1,2,3`, and as the attribute `pages`. |
| Current page (sensor) | The page Tessera Control showed last. |
| Show *name* (button) | One per page: shows it and pauses the rotation (Configure → *Pause after a button*). |

### Brightness

The levels are 100, 60 and 20 % at first. Configure says which level each situation gets; the first situation that
fits wins:

| Situation | Option | Level at first |
|---|---|---|
| The sleep entity is on | *Level while asleep*, only with *Screen off while asleep* off; otherwise the screen goes off | 3 |
| Nobody is home | *Level while nobody is home* | 3 |
| After sunset with every room light off | *Level in a dark room* | 3 |
| After sunset | *Level in the evening* | 2 |
| Otherwise | *Level by day* | 1 |

A light that is unavailable counts as off. Without a presence entity someone is always home; without room lights
the room is never dark.

### Rotation

- When the interval ends, the next page of the rotation shows, round and round.
- When a page joins (the printer starts), it shows at once; when the shown page leaves, the first page shows.
- With one page only, nothing is sent to the screen.
- While the sleep entity is on, the rotation rests.
- When the screen was offline and comes back, it gets its page again.
- The screen turns its "Back to page 1" on again after every restart and firmware update; while the rotation runs,
  Tessera Control turns it off again. With Configure → *Keep "Back to page 1" off* it does so always, also without
  the rotation.

## Limits

- **Home Assistant does not see touches.** The rotation goes on while someone swipes through the pages. Made for a
  screen that is looked at, not used.
- **Home Assistant does not know the page on the glass,** only the one it showed last.
- The screen's action and entities come from Tessera's firmware, not from its documented plugin API: a Tessera update
  may rename them. Written for firmware 0.56.0.

## Development

```sh
pip install -r requirements_test.txt   # Python 3.14
pytest
```

`tests/test_logic.py` needs no Home Assistant: `pytest tests/test_logic.py --noconftest`.

## Licence

MIT, see [LICENSE](LICENSE).
