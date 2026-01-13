import requests
from sspi_flask_app.models.database import sspi_raw_api_data
from sspi_flask_app.api.core.datasets import dataset_collector
from datetime import datetime

@dataset_collector("OECD_MATERN")
def collect_oecd_matern_data(**kwargs):
    """Collect OECD maternity leave data from Child Well-being Dashboard"""
    child_wellbeing_url = "https://www.oecd.org/content/dam/oecd/en/data/dashboards/oecd-child-well-being-dashboard/child-well-being-dashboard-data.xlsx"
    
    yield "Downloading OECD Child Well-being Dashboard Excel file...\n"
    response = requests.get(child_wellbeing_url)
    
    if response.status_code == 200:
        source_info = {
            "OrganizationName": "OECD",
            "OrganizationCode": "OECD",
            "OrganizationSeriesCode": "paidmatern",
            "QueryCode": "paidmatern",
            "SheetName": "Data",
            "DateDownloaded": datetime.now().strftime('%Y-%m-%d'),
            "SourceURL": child_wellbeing_url
        }
        
        sspi_raw_api_data.raw_insert_one(
            response.content,
            source_info,
            **kwargs
        )
        yield "Successfully collected and stored raw OECD child well-being file.\n"
    else:
        raise Exception(f"Failed to download OECD child well-being file: {response.status_code}")
