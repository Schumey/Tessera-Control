# Changelog

## 0.5.0

- The brightness levels are **Brightness level 1**, **2** and **3** now, no longer day, evening and dim. Configure says
  which level each situation gets: by day, in the evening, in a dark room, while nobody is home, and while asleep
  (with *Screen off while asleep* off). At first the same as before: 1 by day, 2 in the evening, 3 otherwise.
- Day, evening and dim become levels 1, 2 and 3 on their own: entity IDs and values stay, only the names change.
- Nobody home and a dark room are two situations now, each with its own level.

## 0.4.0

- New option **Keep "Back to page 1" off** (Configure): the screen turns "Back to page 1" on again after every restart
  and firmware update; Tessera Control turns it off each time, also while the rotation is off. Off at first.
- While the rotation runs, "Back to page 1" turned on is turned off again, not only when the screen comes back.

## 0.3.0

- Tessera Control is now an integration, installed with HACS. It replaces the YAML templates of 0.1.0 and 0.2.0: set
  up the screen under Settings → Devices & services, add its pages on the entry, then turn off the automations and
  remove the package and the dashboard card of the templates.
- Pages are added in the UI, each with a button of its own that shows the page and pauses the rotation.
- The three brightness levels of 0.2.0 stay sliders: number entities **Brightness day**, **evening** and **dim** on
  the screen's device, 100, 60 and 20 % at first.
- The rotation shows a screen its page again when it comes back after being offline.
- Needs Home Assistant 2026.10 or later.

## 0.2.0

- The three brightness levels are helpers now (**Tessera brightness day**, **evening**, **dim**), set with sliders on
  the dashboard card instead of in the automation. A new level applies at once. Set them once after updating: they
  start at 5 %.
- The README shows the `configuration.yaml` lines that load packages as a YAML block.

## 0.1.0

- First version: page rotation with a page list by situation, brightness by situation, a script and a dashboard card
  to jump to a page, as YAML templates.
