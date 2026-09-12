"""Additional post-training numerical checks; no training or model selection."""
import json
from pathlib import Path
import numpy as np
from run_experiment import Model,dataset

def main():
    root=Path(__file__).resolve().parent
    x,y,tr,_=dataset('numeric');errors=[]
    for mode in ('lut2','lut4'):
        model=Model(400,mode)
        checkpoint=np.load(root/f'run/numeric-400-{mode}.npz')
        model.weights=[checkpoint[f'w{i}'].copy() for i in range(3)]
        _,grad=model.gradients(x[tr],y[tr])
        for layer in range(3):
            # Check a nonzero, maximal gradient instead of a disconnected weight.
            i,j=np.unravel_index(np.abs(grad[layer]).argmax(),grad[layer].shape)
            assert abs(grad[layer][i,j])>1e-10
            old=model.weights[layer][i,j];eps=1e-5
            model.weights[layer][i,j]=old+eps;plus=model.gradients(x[tr],y[tr])[0]
            model.weights[layer][i,j]=old-eps;minus=model.gradients(x[tr],y[tr])[0]
            model.weights[layer][i,j]=old
            error=abs((plus-minus)/(2*eps)-grad[layer][i,j])
            assert error<1e-6,(mode,layer,error)
            errors.append(dict(condition=mode,layer=layer,error=float(error)))
    (root/'run/additional_checks.json').write_text(json.dumps(errors,indent=2)+'\n')
    print('Six nonzero trained-state gradients verified; max error',max(a['error'] for a in errors))

if __name__=='__main__':main()
