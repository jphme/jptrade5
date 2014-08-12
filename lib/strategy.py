__author__ = 'jph'


class Strategy(object):
    """
    Strategy reacts on Market Data evets and generates Signal Events
    """

    def __init__(self, queue, datahandler):
        self.queue = queue
        self.datahandler = datahandler


    def calculate_signals(self):
        """
        Calculate Signal Events from Market Data Events
        """
        raise NotImplementedError()


class TestStrategy(Strategy):
    """
    Strategy reacts on Market Data evets and generates Signal Events
    """

    def __init__(self, queue, datahandler):
        super(TestStrategy, self).__init__(queue, datahandler)


    def calculate_signals(self):
        """
        Calculate Signal Events from Market Data Events
        """
        pass