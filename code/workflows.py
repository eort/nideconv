import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe        # pypeline engine
import pypeUtils as pu


def createFSL1stlvl(name,analParam):
    """
    Create an FSL first level GLM modelling Workflow
    """
    fsl.FSLCommand.set_default_output_type('NIFTI_GZ')
    wf = pe.Workflow(name=name)
    wf.base_dir = analParam["workDir"]

    # create nodes
    inputNode = pe.Node(util.IdentityInterface(\
        fields=['events','func','anat','confounds']),
        name="infosource")
    printing = pe.Node(util.Function(input_names=["info"],output_names=[],
                      function=pu.printOutput),name="printing")

    # specify the models
    modelspec = pe.Node(interface=model.SpecifyModel(), name="modelspec")
    level1design = pe.Node(interface=fsl.Level1Design(), name="level1design")

    wf.connect(inputNode,'events',printing,'info')
    return wf

    #modelgen = pe.MapNode(
    #    interface=fsl.FEATModel(),
    #    name='modelgen',
    #    iterfield=['fsf_file', 'ev_files'])

    #modelestimate = pe.MapNode(
    #    interface=fsl.FILMGLS(smooth_autocorr=True, mask_size=5, threshold=1000),
    #    name='modelestimate',
    #   iterfield=['design_file', 'in_file'])





def createExampleWorkflow(name,runSpecs):
    """
    Example to test the outer workflow
    """
    return pe.Workflow(name=name)
