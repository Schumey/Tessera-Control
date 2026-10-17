# Tessera Control

[English](README.md)

Home-Assistant-Konfiguration, die einen [Tessera](https://github.com/MaxGramser/homeassistant_espscreen)-Touchscreen
zu einem Statusdisplay macht, das von selbst läuft:

- **Seitenrotation.** Das Display wechselt in einem einstellbaren Abstand durch seine Seiten.
- **Seiten je nach Situation.** Welche Seiten in der Rotation sind, hängt davon ab, was gerade los ist: die Startseite
  immer, die PC-Seite, solange der PC an ist, die Druckerseite, solange er druckt. Eine neu hinzukommende Seite wird
  sofort gezeigt.
- **Helligkeit je nach Situation.** Eine Stufe für tagsüber, eine für abends, eine wenn niemand da oder der Raum
  dunkel ist (zum Beispiel 100 %, 60 % und 20 %), jede mit einem Slider einstellbar; aus, während du schläfst.
- **Knöpfe fürs Dashboard,** die auf eine Seite springen und die Rotation ein paar Minuten pausieren.

Alles ist reines Home Assistant: ein Package mit Helfern, zwei Automationen, ein Skript und eine Dashboard-Karte. Auf
dem Display wird nichts installiert, und es braucht keinen Firmware-Build.

## So funktioniert es

Tessera meldet für jedes Display eine Action `esphome.<node>_show_page` an Home Assistant, dazu Entities wie
`switch.<screen>_back_to_page_1`, `number.<screen>_normal_brightness` und `button.<screen>_wake`. Diese Konfiguration
nutzt nur diese.

| Datei | Was |
|---|---|
| [`packages/tessera_control.yaml`](packages/tessera_control.yaml) | Die Helfer: Seitenliste (Template-Sensor), Rotations-Timer, Intervall, aktuelle Seite, Rotations-Schalter, die drei Helligkeitsstufen. |
| [`automations/tessera_page_rotation.yaml`](automations/tessera_page_rotation.yaml) | Zeigt die nächste Seite, wenn der Timer abläuft, und reagiert, wenn sich die Seitenliste ändert. |
| [`automations/tessera_brightness.yaml`](automations/tessera_brightness.yaml) | Setzt die Helligkeit nach Anwesenheit, Schlaf, Sonne und den Leuchten im Raum, mit den drei Stufen. |
| [`scripts/tessera_show_page.yaml`](scripts/tessera_show_page.yaml) | Zeigt eine Seite und pausiert die Rotation. Für Dashboard-Knöpfe. |
| [`dashboards/tessera_buttons.yaml`](dashboards/tessera_buttons.yaml) | Eine Karte mit einem Knopf pro Seite, dem Rotations-Schalter und Slidern für die Helligkeitsstufen. |

Die Dateien selbst sind auf Englisch kommentiert.

## Platzhalter

Die Dateien sind eine Vorlage: Ersetze jedes `YOUR_...` durch deine eigene Entity, bevor du sie nutzt.

| Platzhalter | Was hinein gehört | Wo du es findest |
|---|---|---|
| `YOUR_NODE` | Der ESPHome-Node-Name des Displays, mit `_` statt `-` (`dsp-desktop` → `dsp_desktop`) | Tools → Aktionen: nach „show_page“ suchen |
| `YOUR_SCREEN` | Das Präfix der Entities des Displays (`switch.moin_back_to_page_1` → `moin`). Oft nicht gleich dem Node-Namen. | Einstellungen → Geräte → dein Display |
| `binary_sensor.YOUR_SLEEP` | An, während du schläfst | Eigener Sensor oder Helfer |
| `input_boolean.YOUR_PRESENCE` | An, während jemand zu Hause ist | Eigener Sensor oder Helfer |
| `light.YOUR_ROOM_LIGHTS` | Die Leuchte oder Lichtgruppe, die den Raum „hell“ macht | Einstellungen → Entitäten |
| `binary_sensor.YOUR_PC` | An, während der PC läuft (zum Beispiel über die Ping-Integration) | Einstellungen → Entitäten |
| `sensor.YOUR_PRINTER_STATE` | Zustand des Druckers, `printing` während er druckt | Einstellungen → Entitäten |

Die Seiten zählen ab 1. Die Beispiele nutzen 1 für die Startseite, 2 für den PC und 3 für den Drucker: Ändere sie in
der Seitenliste und auf den Knöpfen.

## Einrichten

1. Sicherstellen, dass Home Assistant Packages lädt. In der `configuration.yaml` muss stehen:

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

   Gibt es dort schon eine Zeile `homeassistant:`, nur die Zeile `packages:` darunter einfügen. Ein zweiter Schlüssel
   `homeassistant:` würde den ersten überschreiben.
2. `packages/tessera_control.yaml` nach `/config/packages/` kopieren, die Platzhalter ersetzen, die Konfiguration
   prüfen (Tools → YAML → Konfiguration prüfen) und Home Assistant neu starten.
3. **Tessera rotation interval** auf die gewünschten Sekunden zwischen zwei Seiten stellen (beim ersten Mal steht er
   auf 10), und **Tessera brightness day**, **evening** und **dim** auf die gewünschten Stufen (beim ersten Mal stehen
   sie auf 5 %).
4. Das Skript anlegen: Einstellungen → Automationen & Szenen → Skripte → Skript erstellen → ⋮ → In YAML bearbeiten,
   `scripts/tessera_show_page.yaml` mit deinen Platzhaltern einfügen und als `script.tessera_show_page` speichern.
5. Beide Automationen genauso aus `automations/` anlegen.
6. Eigene Automationen ausschalten, die bisher Seiten oder Helligkeit dieses Displays gesteuert haben.
7. Die Karte aus `dashboards/tessera_buttons.yaml` zu einem Dashboard hinzufügen (Karte hinzufügen → Manuell).
8. **Tessera rotation** einschalten.

## Eine Seite hinzufügen

Im Package eine Zeile zum Template von **Tessera page list** hinzufügen, mit Bedingung und Seitennummer:

```jinja
{% if is_state('media_player.wohnzimmer', 'playing') %}{% set p = p + [4] %}{% endif %}
```

Die Automationen bleiben, wie sie sind. Auf Wunsch einen Knopf in der Karte ergänzen.

## Grenzen

- **Home Assistant sieht keine Berührungen.** Die Rotation läuft weiter, während jemand durch die Seiten wischt.
  Gedacht für ein Display, auf das man schaut, nicht eines, das man bedient.
- **Home Assistant kennt die Seite auf dem Display nicht,** nur die, die es zuletzt selbst gezeigt hat.
- **Ein Display.** Für ein zweites die Dateien kopieren und den Helfern andere Namen geben.
- Die Namen der Action und der Entities kommen aus der Tessera-Firmware, nicht aus ihrer dokumentierten Plugin-API:
  Ein Tessera-Update kann sie umbenennen.

## Lizenz

MIT, siehe [LICENSE](LICENSE).
