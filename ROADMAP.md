# Roadmap

Planned work for Tessera Control. Done items move to the [changelog](CHANGELOG.md).

## Documentation

- [ ] **README (English and German): keep the rotation out of the recorder and the logbook.** The rotation changes
  state every few seconds, which fills the database and the logbook. Add a section that shows how to exclude
  these entities in `configuration.yaml`:

  ```yaml
  recorder:
    exclude:
      entities:
        - timer.tessera_rotation
        - automation.tessera_seitenrotation

  logbook:
    exclude:
      entities:
        - timer.tessera_rotation
        - automation.tessera_seitenrotation
  ```
