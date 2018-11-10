'''
Created on Oct 20, 2016
@author: Rohan Achar
'''
from rtypes.pcc.attributes import dimension, primarykey, predicate
from rtypes.pcc.types.subset import subset
from rtypes.pcc.types.set import pcc_set
from rtypes.pcc.types.projection import projection
from rtypes.pcc.types.impure import impure
from datamodel.search.server_datamodel import Link, ServerCopy

@pcc_set
class Vuqt1Hoangt5MalayaLink(Link):
    USERAGENTSTRING = "Vuqt1Hoangt5Malaya"

    @dimension(str)
    def user_agent_string(self):
        return self.USERAGENTSTRING

    @user_agent_string.setter
    def user_agent_string(self, v):
        # TODO (rachar): Make it such that some dimensions do not need setters.
        pass


@subset(Vuqt1Hoangt5MalayaLink)
class Vuqt1Hoangt5MalayaUnprocessedLink(object):
    @predicate(Vuqt1Hoangt5MalayaLink.download_complete, Vuqt1Hoangt5MalayaLink.error_reason)
    def __predicate__(download_complete, error_reason):
        return not (download_complete or error_reason)


@impure
@subset(Vuqt1Hoangt5MalayaUnprocessedLink)
class OneVuqt1Hoangt5MalayaUnProcessedLink(Vuqt1Hoangt5MalayaLink):
    __limit__ = 1

    @predicate(Vuqt1Hoangt5MalayaLink.download_complete, Vuqt1Hoangt5MalayaLink.error_reason)
    def __predicate__(download_complete, error_reason):
        return not (download_complete or error_reason)

@projection(Vuqt1Hoangt5MalayaLink, Vuqt1Hoangt5MalayaLink.url, Vuqt1Hoangt5MalayaLink.download_complete)
class Vuqt1Hoangt5MalayaProjectionLink(object):
    pass
