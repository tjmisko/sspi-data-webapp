from ....source_utilities.sdg import collectSDGIndicatorData


def collect():
    data = collectSDGIndicatorData("15.5.1")
    return str(type(data))

"""
def validate():


def 

"""