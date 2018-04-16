

#########################
###   CREATE NODES   ####
#########################
fakesubs = [subs[0]]
# just a printi`ng node
printing = pe.Node(util.Function(input_names=["info"],output_names=[],
                      function=printOutput),name="printing")
printing2 = pe.Node(util.Function(input_names=["info"],output_names=[],
                      function=printOutput),name="printing2")
split = pe.Node(util.Function(input_names=["info"],output_names=["result"],
                      function=split),name="split")
#splitruns = pe.Node(util.Function(input_names=["runfiles"],output_names=["runs"],
#                      function=splitRuns),name="splitRuns")
# create sub info
infosource = pe.Node(util.IdentityInterface(fields=['sub_no']),name="infosource")
infosource.iterables = [('sub_no', subs)]

# collect all the subject files
templates = {'anat': 'sub-{sub_no:02d}/anat/sub-{sub_no:02d}_T1w.nii.gz',
             'func': 'sub-{sub_no:02d}/func/sub-{sub_no:02d}*bold.nii.gz',
             'events': 'sub-{sub_no:02d}/func/sub-{sub_no:02d}*events.tsv'}
selectSubs = Node(nio.SelectFiles(templates,base_directory = baseDir),name='selectSubs')

#loadTextFiles = pe.MapNode(util.Function(input_names=['infile'],
#                        output_names=['eventFile'], function = loadTextFile),
#                        iterfield=['infile'], name = 'loadTextFiles')


#splitruns = pe.Node(util.Function(input_names=["runfiles"],output_names=["runs"],
#                      function=splitRuns),name="splitRuns")

###########################
####   CONNECT NODES   ####
###########################

#nested = pe.Workflow(name='nested')
#nested.base_dir = tmpworkDir
#nested.connect(foo,'bar',printing2,'info')

modelfit = pe.Workflow(name='modelfit')
modelfit.base_dir = tmpworkDir
modelfit.connect(infosource,'sub_no',selectSubs,'sub_no')
modelfit.connect(selectSubs,'events',split,'info')
res = modelfit.run()


#modelfit.connect(selectSubs,'events',loadTextFiles,'infile')
#modelfit.connect(splitruns,'runs',loadTextFiles,'infile')
#modelfit.connect(selectSubs,'events',printing,'info')
#modelfit.connect(loadTextFiles,'eventFile',printing2,'info')
#res = modelfit.run()


# make a graph
modelfit.write_graph(graph2use='colored', format='png',dotfilename=op.join(tmpworkDir,'graph_colored.dot'), simple_form=True)
modelfit.write_graph(graph2use='exec', format='png',dotfilename=op.join(tmpworkDir,'graph_exec.dot'), simple_form=True)




# Condition names
condition_names = ['proSwitch', 'reSwitch','proRep','reRep','cue','error']
# Contrasts
cont01 = ['proSwitch>0',      'T', condition_names, [1,0,0,0,0,0]]
cont02 = ['reSwitch>0',       'T', condition_names, [0,1,0,0,0,0]]
cont03 = ['proRep>0',         'T', condition_names, [0,0,1,0,0,0]]
cont04 = ['reRep>0',          'T', condition_names, [0,0,0,1,0,0]]
cont05 = ['proSwitch-proRep', 'T', condition_names, [0.5, 0,-0.5,0,0,0]]
cont06 = ['proRep-proSwitch', 'T', condition_names, [-0.5, 0,0.5,0,0,0]]
cont07 = ['reSwitch-reRep',   'T', condition_names, [0, 0.5,0,-0.5,0,0]]
cont08 = ['reRep-reSwitch',   'T', condition_names, [0, -0.5,0,0.5,0,0]]
cont09 = ['proSC-reSC',       'T', condition_names, [0.5, -0.5,-0.5,0.5,0,0]]
cont10 = ['reSC-proSC',       'T', condition_names, [-0.5, 0.5,0.5,-0.5,0,0]]
cont11 = ['proactive-reactive','T', condition_names, [0.5, -0.5,0.5,-0.5,0,0]]
cont12 = ['reactive-proactive','T', condition_names, [0.5, -0.5,-0.5,0.5,0,0]]
cont13 = ['switch-rep',        'T', condition_names, [0.5, 0.5,-0.5,-0.5,0,0]]
cont14 = ['rep-switch',        'T', condition_names, [-0.5, -0.5,0.5,0.5,0,0]]
cont15 = ['proSwitch-reSwitch','T', condition_names, [0.5, -0.5,0,0,0,0]]
cont16 = ['reSwitch-proSwitch','T', condition_names, [-0.5, 0.5,0,0,0,0]]

contrast_list = [cont01, cont02, cont03, cont04, cont05, cont06, \
                cont07, cont08, cont09, cont10, cont11, cont12,\
                cont13, cont014, cont15, cont16]


for SUB in subs: 
    pass

modelfit = pe.Workflow(name='modelfit')
modelfit.basedir = baseDir
smooth = pe.Node(Smooth(fwhm=fwhm_size),
            output_type = 'NIFTI_GZ',
            name="smooth")
level1 = pe.Node(SpecifyModel(
            subject_info = info,
            input_units='secs',
            time_repetition=cfg['TR'],
            high_pass_filter_cutoff=cfg['highpass_filter'] # set to -1 for no filtering as already have done SG filtering
        ), name='level1')

level1design = pe.Node(Level1Design(
            interscan_interval=analysis_info['TR'],
            bases={'dgamma': {'derivs': True}},
            model_serial_correlations=True,
            contrasts=contrasts), 
            name='l1design')
l1featmodel = Node(FEATModel(), name='l1model')

modelgen = pe.MapNode(
    interface=fsl.FEATModel(),
    name='modelgen',
    iterfield=['fsf_file', 'ev_files'])
modelestimate = pe.MapNode(
    interface=fsl.FILMGLS(smooth_autocorr=True, mask_size=5, threshold=1000),
    name='modelestimate',
    iterfield=['design_file', 'in_file'])








