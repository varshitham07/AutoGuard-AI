# Dataset selection and handling

## Selected dataset: APS Failure at Scania Trucks

- Official source: https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks
- DOI: https://doi.org/10.24432/C51S51
- Provider: Scania CV AB; hosted by the UCI Machine Learning Repository
- Intended task: classify whether a heavy Scania truck's observed failure is associated with the Air Pressure System (APS)
- Published training set: 60,000 rows; 170 operational features plus the class label
- Published official test set: 16,000 rows
- Positive class: APS-related component failure; negative class: failure in a component unrelated to APS
- Missing values are represented as `na`
- The training data is highly imbalanced: 1,000 positive and 59,000 negative cases
- Dataset license: Creative Commons Attribution 4.0 International (CC BY 4.0), per the UCI dataset page

The published challenge cost matrix assigns cost 10 to an unnecessary workshop inspection and cost 500 to a missed APS failure. Evaluation must therefore report recall, precision, PR-AUC, confusion matrix and cost-sensitive results; accuracy alone is misleading.

## Download and local placement

Download the official archive from the UCI page and extract the training CSV to:

`data/raw/aps_failure_training_set.csv`

Keep raw data out of Git. The archive is approximately 54 MB. Preserve the original file and document any preprocessing. Do not mix generated/synthetic records with this real dataset.

## Important scope limitation

This dataset supports heavy-truck APS component-failure classification. It does not directly support passenger-car engine diagnosis, tyre failure prediction, or real-time vehicle telemetry. Do not describe a model trained on it as a universal vehicle-health predictor.

## Citation

APS Failure at Scania Trucks [Dataset]. (2016). UCI Machine Learning Repository. https://doi.org/10.24432/C51S51.
