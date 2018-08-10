
collectSubs = pe.JoinNode(
                    util.IdentityInterface(fields=['fd_subs']),
                joinsource = 'infosource', joinfield = ['fd_subs'], 
                name = 'collectSubs')

transposeSubROIs = pe.Node(
                util.Function(function = pu.transpose,
                    input_names=['aNestedList'],
                    output_names=['transposed_list']),
                 name = 'transposeSubROIs')

FIR_group = pe.MapNode(
                util.Function(function = pu.FIR_group,
                    input_names=['fd'],
                    output_names=['fd_group']),
                 iterfield = ['fd'], name = 'FIR_group')


deconvolve = pe.MapNode(util.Function(function = pu.runDeconvolve,
                    input_names=['signal','dm','parameters','roi'],
                    output_names=['fd']),
                  iterfield = ['signal','roi'], name = 'deconvolve')
deconvolve.inputs.parameters = cfg

outputspec_model = pe.Node(util.IdentityInterface(fields=['fd']),
            name="outputspec_model")

plotFIR_sub = pe.MapNode(util.Function(function = pu.plotSubFIR,
                    input_names=['fd'],
                    output_names=[]),
                  iterfield = ['fd'], name = 'plotFIR_sub')


def extractSubNo(filename):
    import os
    d,f = os.path.split(filename)

    return f.split('_')[0]

def createFileName(sub,roi,connector = '_'):
    return connector.join([sub,roi,'.npy'])

def plotSubFIR(fd):
    """
    Draws the fits per subject per mask
    """
    import matplotlib as mpl
    mpl.use('Agg')
    import matplotlib.pyplot as plt
    import os
    from IPython import embed as shell
    shell()

    fd.type = 'ridge'
    figwidth, figheight = 28, 20
    f = plt.figure(figsize = (figwidth, figheight/2))

    # don't plot all covariates
    fd.relCovariates = [key for key in fd.covariates.keys() if key in ['proSwitch','reSwitch','proRep','reRep']]

    s = f.add_subplot(111)
    s.set_title('FIR responses, with bootstrapped SDs, and rsquare of %s in %s'%(fd.rsq,fd.roi))
    for i,(dec,ev) in enumerate(zip(fd.betas.squeeze(),fd.covariates.keys())):
        if ev not in ['cue','error']:
            plt.plot(fd.timepoints, dec)  
            if not regressType == 'ridge':
                mb = fd.bootstrap_betas_per_event_type[i].mean(axis = -1)
                sb = fd.bootstrap_betas_per_event_type[i].std(axis = -1)
       
                plt.fill_between(fd.timepoints, 
                            mb - sb, 
                            mb + sb,
                            color = 'k',
                            alpha = 0.1)
    plt.legend(fd.relCovariates)
    sns.despine(offset=10)
    plt.savefig(op.join(os.getcwd(),"deconvolved_%s_%s.pdf"%(fd.roi,fd.type)))
    plt.close()


def FIR_group(fd):
    import cPickle as pickle
    import os
    from IPython import embed as shell
    shell()
    print(os.path.join(os.getcwd(),'fd_bunch.pkl'))
    with open(os.path.join(os.getcwd(),'fd_bunch.pkl'), 'wb') as f:
        pickle.dump(fd,f)


def runDeconvolve(signal,dm,parameters,roi):
    """
    Currently only support for FIR deconvolution
    runs deconvolution with settings in parameters on time series
    parameters must have following fields:
    sample_frequency,deconvolution_frequency,deconvolution_interval,
    regressType (lstsq or ridge)
    dm is the Bunch struct with info relevant for the design matrix
    and must have all events, event_names and optionally covariates
    """
    from fir import FIRDeconvolution 
    import numpy as np
    from nipype.interfaces.base import Bunch
    from IPython import embed as shell
    import pickle
    import os
    #shell()
    # extract fields from dm Bunch file
    events = [ np.array(on) for on in dm.onsets]
    event_names = list(dm.conditions)
    durations = list(dm.durations)
    regressors = list(dm.regressors)
    regressor_names= list(dm.regressor_names)

    # make fir object 
    fd = FIRDeconvolution(
            signal = signal, 
            events = events, 
            event_names = event_names, 
            sample_frequency = parameters['sample_frequency'],
            deconvolution_frequency = parameters['deconvolution_frequency'],
            deconvolution_interval = parameters['deconvolution_interval'])

    fd.create_design_matrix()
    if parameters['regressType']  == 'lstsq':
        fd.regress(method = 'lstsq')
        fd.bootstrap_on_residuals(nr_repetitions=1000)
    elif parameters['regressType'] == 'ridge':
        fd.ridge_regress(cv = 10, alphas = np.logspace(-5, 3, 15))

    fd.betas_for_events()
    fd.calculate_rsq()
    


    #out_file = os.path.join(os.getcwd(),'{roi}_fd'.format(roi=roi))
   
    #shell()
    #with open(out_file,'wb') as f:
    #    pickle.dump(fd,f,-1)

    return Bunch(
            betas=fd.betas_per_event_type,
            covariates=fd.covariates,
            timepoints=fd.deconvolution_interval_timepoints,
            roi=roi,
            rsq=fd.rsq,
            type = parameters['regressType'])