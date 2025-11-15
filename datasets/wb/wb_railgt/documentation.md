---
DatasetType: Intermediate
DatasetName: Rail Goods Transported
DatasetCode: WB_RAILGT
Description: Goods transported by railway are the volume of goods transported by railway, measured in metric tons times kilometers traveled.
Unit: Ton-Kilometers (million)
Source:
  OrganizationCode: WB
  OrganizationSeriesCode: IS.RRS.GOOD.MT.K6
  QueryCode: IS.RRS.GOOD.MT.K6
DatasetProcessorFile: sspi_flask_app/api/core/datasets/wb/wb_railgt.py
---
Unit of Measure: Ton-km
Periodicity: Annual

## Statistical Concept and Methodology

### Methodology
Freight traffic on any mode is typically measured in tons and ton-kilometers. A ton-kilometer equals cargo weight transported times distance transported. For railways, an important measure of work performed is gross ton-kilometers, this measure includes rail wagons' empty weight for both empty and loaded movements. This measure of gross ton-kilometers is also called ‘trailing tons' or the total tons being hauled. Sometimes gross ton-kilometer measures include the weight of locomotives used to haul freight trains. The indicator measures the tonne.kilometers of freight on the national territory of the railway. The weight taken into account is the actual weight or chargeable weight of the goods carried. Weight means the quantity of goods in thousands of tonnes. The weight to be taken into consideration includes, in addition to the weight of the goods transported, the weight of packaging and the tare weight of containers, swap bodies, pallets as well as road vehicles transported by rail in the course of combined transport operations. If the goods are transported using the services of more than one railway undertaking (e.g. within the group etc.), when possible the weight of goods should not be counted more than once. The number of tonne-kilometres in millions represents the weight of freight traffic (in millions of tonnes) over the charging distance (in kilometres).

### Statistical concept(s)
Tonne-kilometre (tkm) is a unit of measurement of goods transport which represents the transport of one tonne of goods over a distance of one kilometre. The distance to be covered is the distance actually travelled on the considered network. To avoid double counting each country should count only the tkm performed on its territory. If it is not available, then the distance charged or estimated should be taken into account.
Topic: Infrastructure: Transportation

## Limitations and Exceptions
Data for transport sectors are not always internationally comparable. Unlike for demographic statistics, national income accounts, and international trade data, the collection of infrastructure data has not been "internationalized." The data from UIC is based on voluntary reporting by railway companies, and can show drastic increases or decreases for some of the years due to lack of reporting by some of the companies in that country.


