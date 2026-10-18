# Changelog

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
