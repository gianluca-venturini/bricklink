
class Part(object):

    def __init__(self, element_id, color_id, qty):
        self.element_id = element_id
        self.color_id = color_id
        self.qty = qty

    def __str__(self):
        output = '{element_id},{color_id},{qty}'
        return output.format(**self.__dict__)

    def __eq__(self, other):
        return self.element_id == other.element_id and self.color_id == other.color_id and self.qty == other.qty

    @classmethod
    def from_string(cls, s):
        element_id, color_id, qty = s.split(',')
        return cls(element_id, color_id, int(qty))


class Listing(object):

    def __init__(self, element_id, color_id, qty, price, name, link, store_id, inventory_id):
        self.element_id = element_id
        self.color_id = color_id
        self.qty = qty
        self.price = price
        self.name = name
        self.link = 'http://bricklink.com' + link
        self.store_id = store_id
        self.inventory_id = inventory_id

    def __str__(self):
        output = '{element_id},{color_id},{qty},{price},"{name}",{link},{store_id},{inventory_id}'
        return output.format(**self.__dict__)

    def __repr__(self):
        return self.__str__()


class Store(object):

    def __init__(self, store_id):
        self.store_id = store_id

    def __str__(self):
        output = '{store_id}'
        return output.format(**self.__dict__)
