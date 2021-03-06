import os
import glob
import zipfile
import pymongo

from .sider_parser import load_data
from .sider_parser import sort_key
from hub.dataload.uploader import BaseDrugUploader
import biothings.hub.dataload.storage as storage
from biothings.utils.mongo import get_src_db
from biothings.hub.datatransform import IDStruct

from hub.datatransform.keylookup import MyChemKeyLookup


SRC_META = {
        "url": 'http://sideeffects.embl.de/',
        "license_url" : "ftp://xi.embl.de/SIDER/LICENSE",
        "license_url_short" : "http://bit.ly/2SjPTpx",
        "license": "CC BY-NC-SA 3.0"
        }


def preproc(doc):
    _id = doc["_id"]
    assert _id.startswith('CID')
    assert len(_id) == 12
    return doc


class SiderIDStruct(IDStruct):
    """Custom IDStruct to preprocess _id from sider"""

    def preprocess_id(self,_id):
        assert _id.startswith('CID')
        assert len(_id) == 12
        return int(_id[4:])

    @property
    def id_lst(self):
        id_set = set()
        for k in self.forward.keys():
            for f in self.forward[k]:
                id_set.add(self.preprocess_id(f))
        return list(id_set)

    def find_right(self, ids):
        """Find the first id founding by searching the (_, right) identifiers"""
        inverse = {}
        for rid in self.inverse:
            inverse[self.preprocess_id(rid)] = self.inverse[rid]
        return self.find(inverse,ids)


class SiderUploader(BaseDrugUploader):

    name = "sider"
    #storage_class = storage.IgnoreDuplicatedStorage
    __metadata__ = {"src_meta" : SRC_META}
    keylookup = MyChemKeyLookup([("pubchem","_id")],
                    idstruct_class=SiderIDStruct)
    max_lst_size = 2000

    def load_data(self,data_folder):
        input_file = os.path.join(data_folder,"merged_freq_all_se_indications.tsv")
        self.logger.info("Load data from file '%s'" % input_file)
        docs = self.keylookup(load_data)(input_file)
        for doc in docs:
            # sort the 'sider' list by "sider.side_effect.frequency" and "sider.side_effect.name"
            doc['sider'] = sorted(doc['sider'],
                                  key=lambda x: sort_key(x))
            # take at most self.max_lst_size elements from the 'sider' field
            # See the 'truncated_docs.tsv' file for a list of ids that are affected
            if len(doc['sider']) > self.max_lst_size:
                doc['sider'] = doc['sider'][:self.max_lst_size]

            yield doc

    @classmethod
    def get_mapping(klass):
        mapping = {
                "sider": {
                    "properties": {
                        "stitch": {
                            "properties": {
                                "flat": {
                                    "normalizer": "keyword_lowercase_normalizer",
                                    "type": "keyword",
                                    },
                                "stereo": {
                                    "normalizer": "keyword_lowercase_normalizer",
                                    "type": "keyword",
                                    }
                                }
                            },
                        "indication": {
                            "properties": {
                                "method_of_detection": {
                                    "normalizer": "keyword_lowercase_normalizer",
                                    "type": "keyword",
                                    },
                                "name": {
                                    "type": "text"
                                    }
                                }
                            },
                        "meddra": {
                            "properties": {
                                "type": {
                                    "normalizer": "keyword_lowercase_normalizer",
                                    "type": "keyword",
                                    },
                                "umls_id": {
                                    "normalizer": "keyword_lowercase_normalizer",
                                    "type": "keyword",
                                    }
                                }
                            },
                        "side_effect": {
                            "properties": {
                                "frequency": {
                                    "normalizer": "keyword_lowercase_normalizer",
                                    "type": "keyword",
                                    },
                                "placebo": {
                                    "type": "boolean"
                                    },
                                "name": {
                                    "type": "text"
                                    }
                                }
                            }
                        }
                    }
        }
        return mapping

