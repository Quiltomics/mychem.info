import os
import glob
import pymongo

from .drugbank_parser import load_data
from .exclusion_ids import exclusion_ids
from .drugbank_mapping import drugbank_mapping
from hub.dataload.uploader import BaseDrugUploader
import biothings.hub.dataload.storage as storage
from biothings.utils.common import unzipall
from biothings.utils.exclude_ids import ExcludeFieldsById


SRC_META = {
        "url" : "http://www.drugbank.ca",
        "license_url" : "https://www.drugbank.ca/releases/latest",
        "license_url_short" : "http://bit.ly/2PSfZTD",
        "license" : "CC BY-NC 4.0",
        }


class DrugBankUploader(BaseDrugUploader):

    name = "drugbank"
    storage_class = storage.IgnoreDuplicatedStorage
    __metadata__ = {"src_meta" : SRC_META}
    # See the comment on the ExcludeFieldsById for use of this class.
    exclude_fields = ExcludeFieldsById(exclusion_ids, [
        "drugbank.drug_interactions",
        "drugbank.products",
        "drugbank.mixtures"
    ])

    def load_data(self,data_folder):
        xmlfiles = glob.glob(os.path.join(data_folder,"*.xml"))
        if not xmlfiles:
            self.logger.info("Unzipping drugbank archive")
            unzipall(data_folder)
            self.logger.info("Load data from '%s'" % data_folder)
            xmlfiles = glob.glob(os.path.join(data_folder,"*.xml"))
        assert len(xmlfiles) == 1, "Expecting one xml file, got %s" % repr(xmlfiles)
        input_file = xmlfiles.pop()
        assert os.path.exists(input_file), "Can't find input file '%s'" % input_file
        return self.exclude_fields(load_data)(input_file)

    def post_update_data(self, *args, **kwargs):
        for idxname in ["drugbank.id","drugbank.chebi","drugbank.inchi"]:
            self.logger.info("Indexing '%s'" % idxname)
            # background=true or it'll lock the whole database...
            self.collection.create_index([(idxname,pymongo.HASHED)],background=True)
        # hashed index won"t support arrays, values are small enough to standard
        self.collection.create_index("drugbank.products.ndc_product_code")

    @classmethod
    def get_mapping(klass):
        return drugbank_mapping
