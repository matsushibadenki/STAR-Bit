"""NumPy-only statistical shim, not the original torch pilot."""
import itertools
import numpy as np

def summary(values):
    a=np.asarray(values,dtype=float)
    rng=np.random.default_rng(901)
    boot=a[rng.integers(len(a),size=(10000,len(a)))].mean(1)
    return dict(n=len(a),mean=float(a.mean()),variance=float(a.var(ddof=1)),sd=float(a.std(ddof=1)),
                ci95=np.quantile(boot,[.025,.975]).tolist(),ci_method='seed percentile bootstrap, 10000 resamples')

def comparison(values):
    a=np.asarray(values)
    signs=np.asarray(list(itertools.product((-1,1),repeat=len(a))))
    p=float((np.abs((signs*a).mean(1))>=abs(a.mean())-1e-12).mean())
    return {**summary(a),'p_signflip_two_sided':p}

def holm(items):
    previous=0
    for i,a in enumerate(sorted(items,key=lambda x:x['p_signflip_two_sided'])):
        previous=max(previous,min(1,(len(items)-i)*a['p_signflip_two_sided']))
        a['p_holm']=previous
