# bellevue-code-change-2025
Experiment to find out how well we could produce an updated LUC code just from the city council ordinance that modifies it. 

## Applying ordinance amendments

A script in `crawler/apply_amendments.py` reads the base `LUC.json`, parses the ordinance PDF and writes amended results to `output_json/bellevue/`.

To run:

```bash
python crawler/apply_amendments.py
```

After running, review `output_json/bellevue/amendment_log.json` for any `TODO` notes. Update the JSON or ordinance text as needed and rerun the script to incorporate those changes.
