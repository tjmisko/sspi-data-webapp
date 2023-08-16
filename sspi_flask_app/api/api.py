



def indicator_data_available(IndicatorCode):
    """
    Check if indicator is in database
    """
    return bool(sspi_raw_api_data.find_one({"collection-info.RawDataDestination": IndicatorCode}))