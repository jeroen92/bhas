class Event():
    def __init__(self, subnet, mask, asPath, neighbor, med, announcementType, timestamp, originUpstreamAsCc = None):
        self.subnet = subnet
        self.mask = mask
        self.originAs = asPath[-1]
        self.asPath = ','.join(map(str, asPath)) 
        self.neighbor = neighbor
        self.med = med
        self.announcementType = announcementType
        self.originUpstreamAsCc = originUpstreamAsCc
        self.timestamp = timestamp

    def __hash__(self):
        return (self.prefix, self.mask, self.asPath, self.neighbor, self.med, self.announcementType, self.timestamp).__hash__()

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()
