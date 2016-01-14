class Target():
    def __init__(self, id, prefix, mask, originUpstreamAs, originUpstreamAsCc, asPath, updatedAt):
        self.id = id
        self.prefix = prefix
        self.mask = mask
        self.originUpstreamAs = originUpstreamAs
        self.originUpstreamAsCc = originUpstreamAsCc
        self.asPath = asPath
        self.updatedAt = updatedAt

    def __hash__(self):
        return (self.id, self.prefix, self.mask, self.originUpstreamAs, self.originUpstreamAsCc, self.asPath, self.updatedAt).__hash__()

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()
