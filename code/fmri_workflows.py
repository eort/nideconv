import nipype.pipeline.engine as pe        # pypeline engine
import nipype.algorithms.modelgen as model 
import nipype.interfaces.fsl as fsl   
import nipype.interfaces.utility as util 
import pypeUtils as pu
"""
This is a library of ready-made fmri workflows
"""

def createFSL_firstlvl(name='fsl_1stlvl', cfg=None):
    """Creates a first level analysis workflow with fsl

    ----------
    ::

      name : name of workflow (default: fsl_1stlvl)
      cfg: a dictionary with all parameter specifications
    Inputs::
        inputspec.func_files : functional runs (filename or list of filenames)
        inputspec.subject_info : Bunch files for runs
    Outputs::
        outputspec.cope_files : Contrast estimates for each contrast (list)
        outputspec.varcope_files : Variance estimates for each contrast (list)

    Example
    -------
    Mandatory keywords for cfg (defaults): 
    input_units, TR, parameters_source, highpassfilter,
    bases, model_serial_correlations, contrats,fit_armodel,mask_size,threshold,
    smooth_autocorr

    >>> firstlevel = createFSL_firstlvl('firstlevel',cfg)
    >>> firstlevel.inputs.inputspec.func_files = ['f3.nii', 'f5.nii']
    >>> firstlevel.inputs.inputspec.subject_info = subject_file
    >>> firstlevel.base_dir = '/tmp'
    >>> firstlevel.run() 
    """

    # define in and outputs
    inputspec = pe.Node(util.IdentityInterface(
                fields=['subject_info','func_files']),
            name="inputspec")
    outputspec = pe.Node(util.IdentityInterface(
                fields=['cope_files','varcope_files']),
            name="outputspec")

    # set up 1stllvl model
    level1 = pe.MapNode(model.SpecifyModel(
                    input_units=cfg['input_units'],
                    time_repetition=cfg['TR'],
                    parameter_source =cfg['parameter_source'],
                    high_pass_filter_cutoff=cfg['highpass_filter']),
                iterfield = ['subject_info','functional_runs'],name='level1')

    # Further specify model
    level1Design = pe.MapNode(fsl.Level1Design(
                    interscan_interval=cfg['TR'],
                    bases=cfg['bases'],
                    model_serial_correlations=cfg['model_serial_correlations'],
                    contrasts=cfg['contrasts']), 
                iterfield = ['session_info'],name='level1Design')

    # Set up feat
    l1Feat = pe.MapNode(fsl.FEATModel(), 
                iterfield = ['fsf_file','ev_files'], name='l1Feat')

    # level 1 model estimation
    filmgls= pe.MapNode(fsl.FILMGLS(fit_armodel = cfg['fit_armodel'],
                    mask_size = cfg['mask_size'],threshold = cfg['threshold'],
                    smooth_autocorr=cfg['smooth_autocorr']),
                iterfield = ['design_file','tcon_file','in_file'], 
                name='filmgls')

    # connect first level workflow
    firstlevel = pe.Workflow(name=name)
    firstlevel.connect(inputspec,'subject_info',level1,'subject_info')
    firstlevel.connect(inputspec,'func_files',level1,'functional_runs')
    firstlevel.connect(level1,'session_info',level1Design,'session_info')
    firstlevel.connect(level1Design,'fsf_files',l1Feat,'fsf_file')
    firstlevel.connect(level1Design,'ev_files',l1Feat,'ev_files')
    firstlevel.connect(l1Feat,'con_file',filmgls,'tcon_file')
    firstlevel.connect(l1Feat,'design_file',filmgls,'design_file')
    firstlevel.connect(inputspec,'func_files',filmgls,'in_file')
    firstlevel.connect(filmgls,'copes',outputspec,'cope_files')
    firstlevel.connect(filmgls,'varcopes',outputspec,'varcope_files')

    return firstlevel

def createSusan(name='susan', fwhm = 5):
    """Creates a FSL SUSAN smoothing workflow

    ----------
    ::

      name : name of workflow (default: fsl_1stlvl)
      fwhm: smoothing kernel in mm
    Inputs::
        inputspec.in_files : nifti images to smooth
        inputspec.mask_files : brain masks for niftis
        inputspec.fwhm : smoothing kernel 
    Outputs::
        outputspec.smoothed_file : smoothed file
        outputspec.median : median intensity of something

    Example
    -------
    >>> susan = createSusan('susan',fwhm=5)
    >>> susan.inputs.inputspec.in_files = ['f3.nii', 'f5.nii']
    >>> susan.inputs.inputspec.mask_files = ['f3_mask.nii', 'f5_mask.nii']
    >>> susan.base_dir = '/tmp'
    >>> susan.run() 
    """
    # collect inputs
    inputspec = pe.Node(util.IdentityInterface(
                    fields=['in_files','mask_files','fwhm']),
                name="inputspec")
    inputspec.inputs.fwhm = fwhm

    #  Determine the median value of the functional runs using the mask
    get_median = pe.MapNode(fsl.ImageStats(
                op_string='-k %s -p 50'),
            iterfield=['in_file','mask_file'], name='get_median') 

    #  Determine the median value of the functional runs using the mask
    get_median2 = pe.MapNode(fsl.ImageStats(
                op_string='-k %s -p 50'),
            iterfield=['in_file','mask_file'], name='get_median2') 

    # apply the brain mask to the functional scan (first without dilation)
    maskFunc_1 = pe.MapNode(
                    interface=fsl.ImageMaths(suffix='_mask', op_string='-mas'),
                    iterfield=['in_file','in_file2'],
                name='maskFunc_1')

    # Determine the mean image from each functional run
    meanFunc = pe.MapNode(fsl.MeanImage(),
            iterfield=['in_file'], name='meanFunc')

    # get the USANs. Needs the mean and the median for each func run
    getUSANs = pe.MapNode(util.Function(function = pu.getUsans, 
                        input_names=['mean','median'],
                        output_names=['usan']),
                    iterfield=['mean','median'],name = 'getUSANs')

    # get the brightness median and threshold it at 75%, for SUSAN
    getBtThreshold = pe.MapNode(util.Function(function = pu.getThreshold, 
                        input_names=['value','factor'],
                        output_names=['median_thresholded']),
                    iterfield=['value'],name = 'getBtThreshold')
    getBtThreshold.inputs.factor = 0.75

    # create the actual SUSAN node
    smooth = pe.MapNode(fsl.SUSAN(),
        iterfield=['in_file','brightness_threshold','usans'],name="smooth")

    #Determine the 98th percentile intensities of each functional run
    get98percent = pe.MapNode(fsl.ImageStats(op_string='-p 98'),
                    iterfield=['in_file'],
            name='get98percent')

    # get the command line code to Threshold func data at 10% of 98th percentile
    get98_10op = pe.MapNode(util.Function(function = pu.getthreshop, 
                        input_names=['value','factor'],
                        output_names=['thr']),
                    iterfield=['value'],name = 'get98_10op')
    get98_10op.inputs.factor = 0.1

    # and create the thresholding node
    threshold = pe.MapNode(fsl.ImageMaths(out_data_type='char', 
                        suffix='_thresh'),
                iterfield=['in_file', 'op_string'],
                name='threshold')

    # Dilate the mask with 10% threshold
    dilatemask = pe.MapNode(fsl.ImageMaths(suffix='_dil',op_string='-dilF'),
                        iterfield=['in_file'],
                name='dilatemask')

    # apply the brain mask to func, this time with dilation 
    maskFunc_2 = pe.MapNode(
                    interface=fsl.ImageMaths(suffix='_mask', op_string='-mas'),
                    iterfield=['in_file','in_file2'],
                name='maskFunc_2')

    outputspec = pe.Node(util.IdentityInterface(
                    fields=['smoothed_file','median']),
                name="outputspec")

    # connect nodes
    susan = pe.Workflow(name=name)
    susan.connect(inputspec,'in_files',maskFunc_1,'in_file')
    susan.connect(inputspec,'in_files',maskFunc_2,'in_file')
    susan.connect(inputspec,'in_files',get98percent,'in_file')
    susan.connect(inputspec,'in_files',meanFunc,'in_file')
    susan.connect(inputspec,'mask_files',maskFunc_1,'in_file2')
    susan.connect(get98percent,'out_stat',get98_10op,'value')
    susan.connect(get98_10op,'thr',threshold,'op_string')
    susan.connect(maskFunc_1,'out_file',threshold,'in_file')
    susan.connect(threshold, 'out_file', dilatemask, 'in_file')
    susan.connect(dilatemask, 'out_file', maskFunc_2, 'in_file2')
    susan.connect(dilatemask,'out_file',get_median,'mask_file')
    susan.connect(maskFunc_2,'out_file',get_median,'in_file')
    susan.connect(get_median,'out_stat',getBtThreshold,'value')
    susan.connect(getBtThreshold,'median_thresholded',getUSANs,'median')
    susan.connect(meanFunc,'out_file',getUSANs,'mean')
    susan.connect(getBtThreshold,'median_thresholded',smooth,'brightness_threshold')
    susan.connect(getUSANs,'usan',smooth,'usans')
    susan.connect(maskFunc_2,'out_file',smooth,'in_file')
    susan.connect(inputspec,'fwhm',smooth,'fwhm')
    susan.connect(smooth,'smoothed_file',outputspec,'smoothed_file')
    susan.connect(threshold,'out_file',get_median2,'mask_file')
    susan.connect(inputspec,'in_files',get_median2,'in_file')
    susan.connect(get_median2,'out_stat',outputspec,'median')

    return susan


def create2ndlvl(name='secondlevel'):
    """Creates an FSL 2ndlvl workflow using a MultipleRegressDesign to 
    edit the design matrix.

    ----------
    ::

      name : name of workflow (default: fsl_1stlvl)
      cfg: a dictionary with all parameter specifications
    Inputs::
        inputspec.cope_files : lower level cope files
        inputspec.mask_files : brain mask
        inputspec.varcope_files : lower level varcope files
        inputspec.runInfo : info about regressor and valid copes 
        inputspec.groupContrasts : contrast structure for 2nlvl     
   
    Outputs::
        outputspec.cope_files : 2ndlvl cope_files
        outputspec.varcope_files : 3rdlvl cope_files

    Example
    -------
    >>> secondlevel = create2ndlvl('secondlevel',cfg=secondlvl_cfg)
    >>> secondlevel.inputs.inputspec.cope_files = ['f3.nii', 'f5.nii']
    >>> secondlevel.inputs.inputspec.varcope_files = ['f3.nii', 'f5.nii']
    >>> secondlevel.inputs.inputspec.mask_file = 'f3_mask.nii'
    >>> secondlevel.inputs.inputspec.runInfo = 'runInfo'
    >>> secondlevel.inputs.inputspec.groupContrasts = groupContrasts
    >>> secondlevel.base_dir = '/tmp'
    >>> secondlevel.run() 
    """
    # collect inputs
    inputspec = pe.Node(util.IdentityInterface(
                fields=['cope_files','varcope_files','runInfo','mask_files','groupContrasts']),
            name="inputspec")
    # Transpose (run x cope) to (cope x run)
    transposeCopes = pe.Node(
                    util.Function(function = pu.transposeAndSelect,
                        input_names=['aNestedList','bunch_files'],
                        output_names=['transposedList']),
                    name = 'transposeCopes')
    transposeVarCopes = pe.Node(
                    util.Function(function = pu.transposeAndSelect,
                        input_names=['aNestedList','bunch_files'],
                        output_names=['transposedList']),
                    name = 'transposeVarCopes')

    # based on the 4 event PEs, construct the full contrast matrix
    make2ndlvlCopes = pe.Node(
                    util.Function(function = pu.make2ndLvlDesignMatrix,
                        input_names=['copes'],
                        output_names=['regressors']),
                    name = 'make2ndlvlCopes')

    # first average across runs
    runmergeCOPE = pe.MapNode(interface=fsl.Merge(dimension='t'),
                iterfield = ['in_files'], name='runmergeCOPE')
    runmergeVARCOPE = pe.MapNode(interface=fsl.Merge(dimension='t'),
                iterfield = ['in_files'], name='runmergeVARCOPE')  
    # Second average across copes, so that new contrasts can be 
    # computed, that are specified as regressors in the multiple regression
    copeMerge = pe.Node(interface=fsl.Merge(dimension='t'),
                name='copeMerge')
    varcopeMerge = pe.Node(interface=fsl.Merge(dimension='t'),
                name='varcopeMerge')    

    # regression model to add group level contrasts possible        
    level2model = pe.Node(interface=fsl.MultipleRegressDesign(),
                name='multregmodel')

    # fixed effects 2nd lvl model
    FE=pe.Node(interface=fsl.FLAMEO(run_mode='fe'),
                name='FE')
    # collect outputs
    outputspec = pe.Node(util.IdentityInterface(
                    fields=['cope_files','varcope_files']),
                name="outputspec")

    # connect nodes
    secondlevel = pe.Workflow(name=name)

    secondlevel.connect(inputspec,'runInfo',transposeCopes,'bunch_files')
    secondlevel.connect(inputspec,'cope_files',transposeCopes,'aNestedList')
    secondlevel.connect(inputspec,'runInfo',transposeVarCopes,'bunch_files')
    secondlevel.connect(inputspec,'varcope_files',transposeVarCopes,'aNestedList')
    secondlevel.connect(inputspec,'groupContrasts',level2model,'contrasts')
    secondlevel.connect(inputspec,'mask_files',FE,'mask_file')
    secondlevel.connect(transposeCopes,'transposedList',make2ndlvlCopes,'copes')
    secondlevel.connect(transposeCopes,'transposedList',runmergeCOPE,'in_files')
    secondlevel.connect(transposeVarCopes,'transposedList',runmergeVARCOPE,'in_files')
    secondlevel.connect(runmergeCOPE,'merged_file',copeMerge,'in_files')
    secondlevel.connect(runmergeVARCOPE,'merged_file',varcopeMerge,'in_files')
    secondlevel.connect(copeMerge,'merged_file',FE,'cope_file')
    secondlevel.connect(varcopeMerge,'merged_file',FE,'var_cope_file')
    secondlevel.connect(make2ndlvlCopes,'regressors',level2model,'regressors')
    secondlevel.connect(level2model,'design_mat',FE,'design_file')
    secondlevel.connect(level2model,'design_con',FE,'t_con_file')
    secondlevel.connect(level2model,'design_grp',FE,'cov_split_file')
    secondlevel.connect(FE,'copes',outputspec,'cope_files')
    secondlevel.connect(FE,'var_copes',outputspec,'varcope_files')

    return secondlevel


def createDeconvolutionPreproc(cfg, name='preprocflow'):
    """Does some preprocessing from FMRIPrep data to be ready for deconvolution

    steps include: 
        1) High pass filtering (and related steps)
        2) Conversion to %%-signal change data
        3) Concatenating runs (both func and design matrix)
        
    ----------
    ::
        cfg: a dictionary with all parameter specifications
        name : name of workflow (default: fsl_1stlvl)
      
    Inputs::
        inputspec.func_files : functional niftis for all runs
        inputspec.event_files : when did events happen for all runs
        inputspec.confound_files : confounds to be regressed out of data  
   
    Outputs::
        outputspec.merged_design_matrices : merged Design matrixes across runs
        outputspec.merged_psc_files : merged preprocessed func files

    """

    inputspec_preproc = pe.Node(util.IdentityInterface(
                    fields=['func_files','event_files','confound_files']),
                name="inputspec_preproc")

    # select one run from the list of all runs
    selectSingleRun = pe.Node(util.Function(input_names=['aList','idx'],
                            output_names=['first_item'],function=pu.selectFromList),
                        name="selectSingleRun")
    selectSingleRun.inputs.idx = 0 # get the first item
    #highpass filter
    hpFilter = pe.MapNode(fsl.TemporalFilter(),
                    iterfield = ['in_file'],name = 'hpFilter')
    hpFilter.inputs.highpass_sigma = (cfg['hpfilter_cutoff']/(2*cfg['TR'])) # corresponds to 50 s
    # Add back the mean removed by the hp filter 
    meanFunc_hp = pe.MapNode(fsl.MeanImage(),
                iterfield=['in_file'], name='meanFunc_hp')
    addmean = pe.MapNode(fsl.BinaryMaths(operation='add'),
                    iterfield=['in_file', 'operand_file'],
                name='addmean')

    # compute percent signal change
    computePSC = pe.MapNode(util.Function(input_names=['in_file'],
                        output_names=['out_file'],function=pu.computePSC),
                    iterfield =['in_file'], name="computePSC")

    # concatenate runs
    mergeRuns = pe.Node(interface=fsl.Merge(dimension='t'),
                name='mergeRuns')

    # get design matrix info for each run
    collectRunInfo = pe.MapNode(util.Function(function = pu.createDesignInfo,
                        input_names=['evFile','confoundFile','parameters'],
                        output_names=['runInfo','runPickle']),
                    iterfield=['evFile','confoundFile'],name = 'collectRunInfo')
    collectRunInfo.inputs.parameters = cfg

    # combine all runs into one Bunch struct (analog to copemerge)
    mergeRunInfo = pe.Node(util.Function(function = pu.mergeDesignInfo,
                        input_names=['bunch_files'],
                        output_names=['merged_design_matrices']),
                    name = 'mergeRunInfo')

    # collect relevant output
    outputspec_preproc = pe.Node(util.IdentityInterface(
                    fields=['merged_psc_files','merged_design_matrices']),
                name='outputspec_preproc')

    # connect preproc workflow
    preprocflow = pe.Workflow(name=name)
    preprocflow.connect(inputspec_preproc,'confound_files',collectRunInfo,'confoundFile')
    preprocflow.connect(inputspec_preproc,'event_files',collectRunInfo,'evFile')
    preprocflow.connect(inputspec_preproc,'func_files',hpFilter,'in_file')
    preprocflow.connect(inputspec_preproc,'func_files',meanFunc_hp,'in_file')
    preprocflow.connect(meanFunc_hp,'out_file',addmean,'operand_file')
    preprocflow.connect(hpFilter,'out_file',addmean,'in_file')

    preprocflow.connect(addmean,'out_file',computePSC,'in_file')
    preprocflow.connect(computePSC,'out_file',mergeRuns,'in_files')
    preprocflow.connect(computePSC,'out_file',selectSingleRun,'aList')
    preprocflow.connect(mergeRuns,'merged_file',outputspec_preproc,'merged_psc_files')
    preprocflow.connect(collectRunInfo,'runInfo',mergeRunInfo,'bunch_files')
    preprocflow.connect(mergeRunInfo,'merged_design_matrices',outputspec_preproc,'merged_design_matrices')

    return preprocflow


def createMaskFlow(cfg, name='maskflow'):
    """Takes some input mask niftis. Makes sure they are in the fmriprep native space 
        (if not already) and returns those masks (together with the mask names)

    ----------
    ::
        cfg: a dictionary with all parameter specifications
        name : name of workflow (default: maskflow)
      
    Inputs::
        inputspec.mask_ref : functional niftis for all runs
        inputspec.mask_files : the masks to be converted
   
    Outputs::
        outputspec.mask_files : path to mask files
        outputspec.mask_names : Labels without the path

    """

    # collect mask flow esssentials
    inputspec_mask = pe.Node(util.IdentityInterface(
                    fields=['mask_files','reference']),
                name='inputspec_mask')
    inputspec_mask.inputs.reference=cfg['mask_ref']


    # change resolution of MNI masks to fmriprep space
    MNI2FMRIPREP = pe.MapNode(fsl.FLIRT(), 
            iterfield = ['in_file'], name = 'MNI2FMRIPREP')
    MNI2FMRIPREP.inputs.no_search = cfg['no_search']
    MNI2FMRIPREP.inputs.uses_qform = cfg['uses_qform']
    MNI2FMRIPREP.inputs.apply_xfm = cfg['apply_xfm']
    MNI2FMRIPREP.inputs.interp = cfg['interp']

    # threshold the transformed masks and binarize to counteract edge-blurring
    binarizeMasks = pe.MapNode(fsl.Threshold(thresh = cfg['threshold'],args = '-bin'), 
            iterfield = ['in_file'], name = 'binarizeMasks')

    extractMaskNames = pe.MapNode(util.Function(function = pu.extractMaskNames,
                        input_names=['mask_file'],
                        output_names=['mask_name']),
                      iterfield = ['mask_file'], name = 'extractMaskNames')

    outputspec_masks = pe.Node(util.IdentityInterface(
        fields=['mask_files','mask_names']),
                name="outputspec_masks")

    maskflow = pe.Workflow(name=name)
    maskflow.connect(inputspec_mask,'reference',MNI2FMRIPREP,'reference')
    maskflow.connect(inputspec_mask,'mask_files',MNI2FMRIPREP,'in_file')
    maskflow.connect(MNI2FMRIPREP,'out_file',outputspec_masks,'mask_files')
    maskflow.connect(MNI2FMRIPREP,'out_file',extractMaskNames,'mask_file')
    maskflow.connect(extractMaskNames,'mask_name',outputspec_masks,'mask_names')

    return maskflow