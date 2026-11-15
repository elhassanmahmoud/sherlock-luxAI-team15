"""One frozen equal-weight R8 midpoint in two views, after the original V14 choice."""
from scripts.r3_diagonal import TwoViews,digest
from scripts.selective_advice_agent import SelectiveAdviceAgent

MIDPOINT="51a52f0453d5ac8e9a4ea70b3792572356761054cb2890520005160f77097cf2"


class MidpointDiagonalAgent(SelectiveAdviceAgent):
    def __init__(self,*args,advice_path,mode="movement",**kwargs):
        if mode!="movement" or digest(advice_path)!=MIDPOINT:
            raise ValueError("Only the original pre-registered midpoint and movement mode are eligible")
        super().__init__(*args,advice_path=advice_path,mode=mode,**kwargs)
        if len(self.members)!=1 or not self.sap_own_tile:
            raise ValueError("Expected the registered single movement model")
        self.members=[TwoViews(self.members[0])]
