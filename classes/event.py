class Event():
    def __init__(self, subnet, mask, neighbor, announcementType, timestamp, updateType, originUpstreamAsCc = None, asPath = None, med = None,):
        self.subnet = subnet
        self.mask = mask
        self.originAs = asPath[-1]
        self.asPath = ','.join(map(str, asPath)) 
        self.neighbor = neighbor
        self.med = med
        self.announcementType = announcementType
        self.updateType = updateType
        self.originUpstreamAsCc = originUpstreamAsCc
        self.timestamp = timestamp

    def __hash__(self):
        return (self.prefix, self.mask, self.asPath, self.neighbor, self.med, self.announcementType, self.timestamp).__hash__()

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()
