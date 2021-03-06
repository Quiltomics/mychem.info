import pandas as pd
import json


def load_data(input_file):

    unii = pd.read_csv(input_file, sep='\t', low_memory=False, dtype=str)
    unii.rename(columns={'MF': 'molecular_formula',
                         'PT': 'preferred_term',
                         'RN': 'registry_number'}, inplace=True)
    unii.columns = unii.columns.str.lower()

    # half of them don't have inchikeys
    # set the primary key to inchikey and fill in missing ones with unii
    unii['_id'] = unii.inchikey
    unii['_id'].fillna(unii.unii, inplace=True)

    dupes = set(unii._id) - set(unii._id.drop_duplicates(False))
    records = [{k:v for k,v in record.items() if pd.notnull(v)} for record in unii.to_dict("records") if record['_id'] not in dupes]
    records = [{'_id': record['_id'], 'unii': record} for record in records]
    # take care of a couple cases with identical inchikeys
    for dupe in dupes:
        dr = unii.query("_id == @dupe").to_dict("records")
        dr = [{k:v for k,v in record.items() if pd.notnull(v)} for record in dr]
        records.append({'_id': dupe, 'unii': dr})
    for record in records:
        if isinstance(record['unii'], dict):
            del record['unii']['_id']
        else:
            for subr in record['unii']:
                del subr['_id']
        yield record

