import pkg_resources

def get_doc_path(filename:str):
    return pkg_resources.resource_filename(__name__, filename)
