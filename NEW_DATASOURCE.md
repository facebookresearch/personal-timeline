# Adding a New Data Source
There are two ways to add a new data source depending on the complexity of input.
If you have a simple non-nested CSV or JSON file, it's quite straightforward and can be done by updating some configurations.
For more complex cases, writing a custom importer is required.
Information on both scenarios is detailed below.

## Adding Data Source Configs
[data_source.json](src/common/bootstrap/data_source.json) keeps track of all sources and should be updated 
irrespective of the path you choose to add the new source.
This file contains a list of all data sources that are processed by the importer. 
In code, these configs are deserialized to class structure defined in [import_configs.py](src/common/objects/import_configs.py).
- Refer to [Class Hierarchy](src/common/objects/import_configs.py) to properly add an entry to 
[data_source.json](src/common/bootstrap/data_source.json). Give a unique source id to your data source.


## Simple Non-nested CSV and JSONs
If you have a simple non-nested CSV or JSON file, you can simply use the generic CSV/JSON importer provided once the new data source is configured properly.
Steps to follow:
- Follow steps in "Adding Data Source Configs" section to update [data_source.json](src/common/bootstrap/data_source.json) file.
- Rerun [init.py](src/init.py) to create source directory for new sources.
- Add data files to source directory.
- Make sure `ingest_new_data` is set to True in [ingest.conf](conf/ingest.conf)
- Re-run the backend docker image to ingest data from new sources.

## More complex Inputs
Write a custom importer following these guidelines 
- Follow steps in "Adding Data Source Configs" section to update [data_source.json](src/common/bootstrap/data_source.json) file.
- Extend your custom importer from [GenericImporter](src/ingest/importers/generic_importer.py) class; 
    implement the function `import_data` and use the configurations as appropriate to create LLEntry objects(Refer to available custom importers)
- Store class file under [importers](src/ingest/importers)
- Update  `generic_importer_workflow.py`; add call to your class in the `if...else` loop of the `start_import` function. Alternatively, contribute to fix this class using configs.

When writing new importer for Photos, you may find it useful to extend `PhotoImporter` instead of `GenericImporter`. 
We started with simple Photo imports so `PhotoImporter` was written to reduce code duplication.
Creating `GenericImporter` was an afterthought and there is room for improving this model of extension to refactor, or even combine
these two importer classes in the future. 
