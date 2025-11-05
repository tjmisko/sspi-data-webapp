---
DatasetType: Intermediate
DatasetName: Rail Network Intensity
DatasetCode: WB_RAILLN
Description: The total length of rail line in the country operated for passenger transport, goods transport, or both (in kilometers).
Source:
  OrganizationCode: WB
  OrganizationSeriesCode: IS.RRS.TOTL.KM
  QueryCode: IS.RRS.TOTL.KM
DatasetProcessorFile: sspi_flask_app/api/core/datasets/wb/wb_railln.py
---

WorldBank Gets the Raw Data from this source: Railisa Database, International
Union of Railways ( UIC ), uri: uic-stats.uic.org

## Notes from original source

Internation Union of Railways (UIC Railisa Database): Var 1112 Total length of
lines worked at the end of the year. Gauge: N standard gauge (1,435 m) L broad
gauge (exact rail gauge inserted); E narrow gauge (exact rail gauge inserted).
The length of railway lines worked is obtained by taking these sections
including main-line track listed in the Capital Expenditure Account. Sections
not worked are deducted only in cases where they are permanently out of use
that is to say, if they are no longer maintained in working order. Lines
temporarily out of use continue to form part of the length of lines worked. The
length of a section is measured in the middle of the section, from centre to
centre of the passenger buildings, or of the corresponding service buildings,
of stations which are shown as independent points of departure or arrival for
the conveyance of passengers or freight. If the boundary of the rail network
falls in open track, the length of the section is measured up to that point.
The section situated between a station approach and the join to the main line
of two lines or more which is used by all trains in either direction over these
lines, is only counted once. However, if for one or more of these lines, tracks
are normally allocated, the length of these lines is counted separately. On the
other hand, if between two stations there are one or more parallel tracks
(siding-lines) to the main line, only the length of the latter is counted. In
the case of regular lines worked exclusively during part of the year (seasonal
lines), their length is included in the end-of-year statement.

Periodicity: Annual

## Statistical Concept and Methodology

### Methodology
Rail lines are the length of railway route available for train service,
irrespective of the number of parallel tracks. It includes railway routes that
are open for public passenger and freight services and excludes dedicated
private resource railways. Gauge: N (standard gauge: 1,435 m); L (broad gauge:
exact rail gauge inserted); E (narrow gauge: exact rail gauge inserted). The
length of railway lines worked is obtained by taking these sections including
main-line track listed in the Capital Expenditure Account. Sections not worked
are deducted only in cases where they are permanently out of use, that is, if
they are no longer maintained in working order. Lines temporarily out of use
continue to form part of the length of lines worked. The length of a section is
measured in the middle of the section, from center to the center of the
passenger buildings, or of the corresponding service buildings, of stations
which are shown as independent points of departure or arrival for the
conveyance of passengers or freight. If the boundary of the rail network falls
in open track, the length of the section is measured up to that point. The
section situated between a station approach and the join to the main line of
two lines or more which is used by all trains in either direction over these
lines, is only counted once. However, if for one or more of these lines, tracks
are normally allocated, the length of these lines is counted separately. If
between two stations there are one or more parallel tracks (siding-lines) to
the main line, only the length of the latter is counted. In the case of regular
lines worked exclusively during part of the year (seasonal lines), their length
is included in the end-of-year statement (Var 1112: Total length of lines
worked at the end of the year in the Railisa database). 

### Statistical Concepts
Railway line: one or more adjacent running tracks forming a route between two
points. Where a section of network comprises two or more lines running
alongside one another, there are as many lines as routes to which tracks are
allotted exclusively.


