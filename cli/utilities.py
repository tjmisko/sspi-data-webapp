def full_name(name):
    if name == "raw":
        return "sspi_raw_api_data"
    if name == "meta" or name == "metadata":
        return "sspi_metadata"
    if name == "clean":
        return "sspi_clean_api_data"
    return name
