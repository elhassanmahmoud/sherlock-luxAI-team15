import torch
from scripts.r3_view_consensus import proposals,scores
from scripts.r3_consensus_offline import counters,checks


def decide(a,b,base=0,allowed=(0,1,2,3,4,5)):
    a,b=torch.tensor([a],dtype=torch.float32),torch.tensor([b],dtype=torch.float32)
    mask=torch.tensor([[i in allowed for i in range(6)]])
    return tuple(x.item() for x in proposals(a,b,(a+b)*.5,mask,torch.tensor([base])))


def test_confident_mean_can_disagree_between_the_two_original_legal_choices():
    assert decide([0,10,0,-9,-9,-9],[0,0,1,-9,-9,-9])==(1,0,False)
    assert decide([0,10,0,-9,-9,-9],[0,0,1,-9,-9,-9],base=5)==(5,5,False)


def test_mask_shared_before_all_three_argmax_choices_and_threshold_only_applies_to_mean():
    a=[3,2,0,99,-9,-9]
    b=[9,2,0,98,-9,-9]
    assert decide(a,b,base=1,allowed=(0,1))==(0,0,True)
    assert decide([0,.01,-5,-5,-5,-5],[0,.01,-5,-5,-5,-5],base=4)==(4,4,True)
    assert decide([0,1,0,0,0,9],[0,1,0,0,0,9],base=0)==(0,0,True)


def test_reflection_aligns_scores_in_world_direction_not_transposed_numeric_class():
    class Net:
        def forward_all(self,x,i,pos,f):
            positive=pos[0,0].item()==2
            return torch.tensor([[0.,0.,9.,1.,0.,0.]] if positive else [[0.,0.,1.,9.,0.,0.]]),None,None
    v=scores(Net(),torch.zeros((1,16,24,24)),torch.tensor([0]),torch.tensor([[2,3]]),torch.zeros((1,79)))
    assert v[0].argmax()==v[1].argmax()==v[2].argmax()==2


def test_strict_teacher_improvement_and_no_automatic_credit_for_merely_abstaining():
    old=torch.tensor([1,1,1])
    new=torch.tensor([0,0,0])
    base=new.clone()
    bits=counters(old,new,torch.zeros(3,dtype=torch.bool),base,torch.tensor([0,1,2]))
    totals={k:int(v.sum()) for k,v in bits.items()}
    assert (totals["gained"],totals["lost"],totals["neutral"])==(1,1,1)
    assert checks(totals)==dict(different_final_class=True,more_correct_reverts=False)
