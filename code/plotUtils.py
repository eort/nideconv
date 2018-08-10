import seaborn as sns
import matplotlib.pyplot as pl
import numpy as np
def plot_significance_lines(fd, colors,limits):
    """
    """
    import mne
    #shell()
    # create 2d matrix like dataframe across subjects, with events as index
    sub_data = fd.groupby(['sub','eventTypes','time'])['betas'].mean().unstack('sub')
    time_points = fd.time.unique()

    for evI,ev in enumerate(fd.eventTypes.unique()):
        timeseries = sub_data.loc[ev].values.T
        disp = np.linspace(limits[0],limits[1],50)
        disp_range = [disp[evI+1],disp[evI+1]]
        # run permutation test
        t_clust, clust_times, p_values, H0 = mne.stats.permutation_cluster_1samp_test(timeseries[...])
        for times, p_val in zip (clust_times, p_values):
            if p_val < 0.05:
                s = np.arange(time_points.shape[0])[times]
                if type(colors[ev]) == list:
                    pl.plot([time_points[s[0]], time_points[s[-1]]], disp_range,  linewidth = 6.0, alpha = 0.8,color =colors[ev][0])
                    pl.plot([time_points[s[0]], time_points[s[-1]]], disp_range, dashes=[4, 4], linewidth = 6.0, alpha = 0.8,color =colors[ev][1])
                else:
                    pl.plot([time_points[s[0]], time_points[s[-1]]], disp_range, linewidth = 6.0, alpha = 0.8,color =colors[ev])
                print("Cluster p-value %1.5f between timepoints %1.5f and %1.5f, in color"%(p_val, time_points[s[0]], time_points[s[-1]]))


def plotTimeCourse(fd,plot_cfg = None):
    """
    fd is the dataframe with FIR results
    plot_cfg carries plotting options. To be implemented!
    """
    ROI = fd.roi.unique()
    # plot time series individually per event 
    f = pl.figure(figsize = (28,20))
    # set style
    sns.set(font_scale=2.5,)
    sns.set_style('white')
    # choose colors
    colors = dict()
    cm = pl.get_cmap('Paired')
    pot_colors = [cm.colors[i] for i in range(1,2*len(fd.eventTypes.unique())-1,2)]
    for evI,ev in enumerate(fd.eventTypes.unique()):
        conds = ev.split('-')
        if len(conds)>1:
            colors[ev] = [colors[conds[0]],colors[conds[1]]]
        else:
            colors[ev] = pot_colors[evI]

    plot_fd = fd[fd["condDiff"]=='no']

    # plot timecourse
    ax = f.add_subplot(111)
    ax.set_title('FIR, rsquare %1.3f, %s'%(fd['rsq'].mean(),ROI))
    sns.tsplot(data=plot_fd,condition = 'eventTypes',unit= 'sub',value='betas',time='time',legend = True,ci=68,color = colors)  
    pl.tight_layout()        
    sns.despine(offset=10)
    # lines for orientation
    pl.axhline(0, lw=0.5, alpha=0.5, color = 'k')
    pl.axvline(0, lw=0.5, ls = '--', alpha=0.5, color = 'k')
    limits = [fd.betas.values.mean()-2*fd.betas.values.std(),\
                fd.betas.values.mean()+2*fd.betas.values.std()]
    ax.set(ylim=(limits))

    # plot significant lines
    plot_significance_lines(fd,colors,limits)

    # save figure
    pl.savefig(plot_cfg['outfile'])
    pl.close()    