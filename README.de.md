# Tessera Control

[English](README.md)

Eine Home-Assistant-Integration, die einen [Tessera](https://github.com/MaxGramser/homeassistant_espscreen)-Touchscreen
zu einem Statusdisplay macht, das von selbst läuft:

- **Seitenrotation.** Das Display wechselt in einem einstellbaren Abstand durch seine Seiten.
- **Seiten je nach Situation.** Jede Seite ist immer in der Rotation, oder nur, solange eine Entität bestimmte
  Zustände hat: die PC-Seite, solange der PC an ist, die Druckerseite, solange er druckt. Eine neu hinzukommende Seite
  wird sofort gezeigt.
- **Helligkeit je nach Situation.** Drei Helligkeitsstufen, jede per Schieberegler, und für jede Situation (Tag,
  Abend, dunkler Raum, niemand da) die Stufe, die sie bekommt; während du schläfst, geht das Display aus.
- **Ein Knopf pro Seite** für Dashboards und Skripte: Er zeigt die Seite und pausiert die Rotation ein paar Minuten.

Auf dem Display wird nichts installiert, und es braucht keinen Firmware-Build: Die Integration nutzt die Aktion und
die Entitäten, die die Tessera-Firmware ohnehin an Home Assistant meldet.

## Installieren

Mit [HACS](https://hacs.xyz):

1. HACS → ⋮ → **Benutzerdefinierte Repositories**: `https://github.com/Schumey/Tessera-Control` mit Typ
   **Integration** hinzufügen.
2. In HACS nach **Tessera Control** suchen und herunterladen.
3. Home Assistant neu starten.

Von Hand: `custom_components/tessera_control` nach `config/custom_components/` kopieren und neu starten.

Ab Home Assistant 2026.10.

## Einrichten

1. Einstellungen → Geräte & Dienste → **Integration hinzufügen** → **Tessera Control**, und das Display wählen. Es
   muss online sein. Mit **Seiten auf dem Display** (optional) werden alle Seiten gleich mit angelegt: „Seite 1“ bis
   „Seite n“, jede immer in der Rotation.
2. Am Eintrag der Integration **Seite hinzufügen** → **Alle Seiten auf einmal** macht dasselbe später; Seitennummern,
   die es schon gibt, bleiben. Mit **Eine Seite** kommt eine Seite einzeln dazu:
   - **Name**: steht auf dem Knopf der Seite.
   - **Seitennummer**: die Nummer der Seite auf dem Display; die erste Seite ist 1.
   - **In der Rotation**: *Immer*, oder *Wenn eine Entität einen dieser Zustände hat* mit Entität und Zuständen
     (für einen Drucker: `printing`, `paused`).
3. Unter **Konfigurieren** legst du fest, wonach sich die Helligkeit richtet: eine Schlaf-Entität, eine
   Anwesenheits-Entität, die Leuchten im Raum (alles optional), und welche Stufe jede Situation bekommt.
4. Auf der Geräteseite des Displays **Seitenrotation** und **Automatische Helligkeit** einschalten.

Seiten lassen sich am Eintrag jederzeit ändern oder löschen.

## Was du bekommst

Alles auf der Geräteseite des Displays:

| Entität | Was |
|---|---|
| Seitenrotation (Schalter) | Rotation an oder aus. Aus gibt dem Display sein eigenes „Back to page 1“ zurück, außer mit *„Back to page 1“ immer aus*. |
| Automatische Helligkeit (Schalter) | Helligkeit je nach Situation an oder aus. Aus behält die letzte Helligkeit. |
| Rotationsintervall (Zahl) | Sekunden zwischen zwei Seiten, 10 bis 600. |
| Helligkeit Stufe 1, 2, 3 (Zahlen) | Die drei Stufen, 5 bis 100 %, als Schieberegler. Eine neue Stufe gilt sofort. |
| Seiten in der Rotation (Sensor) | Die Seiten, die gerade in der Rotation sind, etwa `1,2,3`, und als Attribut `pages`. |
| Aktuelle Seite (Sensor) | Die Seite, die Tessera Control zuletzt gezeigt hat. |
| *Name* zeigen (Knopf) | Einer pro Seite: zeigt sie und pausiert die Rotation (Konfigurieren → *Pause nach einem Knopf*). |

### Helligkeit

Die Stufen stehen anfangs auf 100, 60 und 20 %. Unter Konfigurieren legst du fest, welche Stufe jede Situation
bekommt; die erste passende Situation gewinnt:

| Situation | Option | Stufe anfangs |
|---|---|---|
| Die Schlaf-Entität ist an | *Stufe beim Schlafen*, nur mit *Display aus beim Schlafen* aus; sonst geht das Display aus | 3 |
| Niemand zu Hause | *Stufe, wenn niemand da ist* | 3 |
| Nach Sonnenuntergang und alle Raumleuchten aus | *Stufe bei dunklem Raum* | 3 |
| Nach Sonnenuntergang | *Stufe abends* | 2 |
| Sonst | *Stufe tagsüber* | 1 |

Eine nicht verfügbare Leuchte gilt als aus. Ohne Anwesenheits-Entität gilt immer jemand als zu Hause; ohne
Raumleuchten ist der Raum nie dunkel.

### Rotation

- Wenn das Intervall abläuft, kommt die nächste Seite der Rotation, immer im Kreis.
- Kommt eine Seite hinzu (der Drucker startet), wird sie sofort gezeigt; fällt die gezeigte Seite weg, kommt die
  erste Seite.
- Bei nur einer Seite wird nichts ans Display geschickt.
- Solange die Schlaf-Entität an ist, ruht die Rotation.
- War das Display offline und ist wieder da, bekommt es seine Seite erneut.
- Das Display schaltet sein „Back to page 1“ nach jedem Neustart und Firmware-Update wieder ein; während die Rotation
  läuft, schaltet Tessera Control es wieder aus. Mit Konfigurieren → *„Back to page 1“ immer aus* immer, auch ohne
  Rotation.

## Grenzen

- **Home Assistant sieht keine Berührungen.** Die Rotation läuft weiter, während jemand durch die Seiten wischt.
  Gedacht für ein Display, auf das man schaut, nicht eines, das man bedient.
- **Home Assistant kennt die Seite auf dem Display nicht,** nur die, die es zuletzt selbst gezeigt hat.
- Aktion und Entitäten des Displays kommen aus der Tessera-Firmware, nicht aus ihrer dokumentierten Plugin-API: Ein
  Tessera-Update kann sie umbenennen. Geschrieben für Firmware 0.56.0.

## Entwicklung

```sh
pip install -r requirements_test.txt   # Python 3.14
pytest
```

`tests/test_logic.py` braucht kein Home Assistant: `pytest tests/test_logic.py --noconftest`.

## Lizenz

MIT, siehe [LICENSE](LICENSE).
