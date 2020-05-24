import xml.etree.ElementTree as ET

from models import Part


class XmlFormatError(Exception):

    def __init__(self, item):
        self.item = ET.tostring(item)

    def __str__(self):
        return repr(self.item)


def load_parts(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    parts = []
    for item in root.findall('ITEM'):
        try:
            part_id = item.find('ITEMID').text
            color_id = item.find('COLOR').text
            qty = int(item.find('MINQTY').text)
        except:
            raise XmlFormatError(item)
        if part_id is None or color_id is None or qty is None:
            raise XmlFormatError(item)
        part = Part(part_id, color_id, qty)
        print('loading part', part)
        parts.append(part)
    return parts
