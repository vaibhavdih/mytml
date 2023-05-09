from mytml.vsdx_parser import VsdxParser 
from mytml.factory import VisioComponentFactory, VisioConnectorFactory

class Loader:
    def __init__(self, source):
        self.visio = None
        self.source = source
        self.parser = VsdxParser(VisioComponentFactory(), VisioConnectorFactory())

    def get_visio(self):
        return self.visio

    def load(self):
        try:
            self.visio = self.parser.parse(self.source.name)
        except Exception as e:
            print(e)
            raise Exception(f"Diagram file is not valid {e.__class__.__name__} {e.__str__()}")