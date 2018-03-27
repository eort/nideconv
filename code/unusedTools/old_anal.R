# Analysis of Beck_triple
# same as the rest. critical condition comparison is forced vs. free choice
# Made by Eduard Ort, 2016

library(afex) # transform between long and wide
# loading packages, need to be installed first
library(reshape2) # tools for splitting, applying and combining data
library(plyr) # tools for splitting, applying and combining data
library(ggplot2) # pretty plots
library(magrittr) # improve readability of pipeing commands
library(lattice) # plotting extra functions
library("grid") # to be able to use `unit` function in ggplot2
library(BayesFactor)


rm(list = ls())
#change working directory
#loading user-defined functions
baseDir <- '~/projects/BA_fMRI/'
setwd('~/projects/Exptools/code/')
source('preproc.R')
setwd(baseDir)
datafiles <- dir(baseDir,pattern = "sub-[[:digit:]]{2}-[[:digit:]]{2}_RFILES.csv",full.names = TRUE,recursive = TRUE)
plotDir <- paste(baseDir,'results/',sep="")
outDir <- paste(baseDir,'stat_csv/',sep="")
dir.create(outDir, showWarnings = FALSE)
dir.create(plotDir, showWarnings = FALSE)
data <- ldply(datafiles,read.csv) 
#write.csv(data, file = paste(outDir,"allData.csv",sep=""),row.names=FALSE)

excl <- c(18,20,24)
# <- data[which(!(data$color_switch == 'None')),]
#data <- data[which(!(data$target_category == 'None')),]

data$switch_interval <- as.numeric(as.character(data$switch_interval))
data$switch_interval[data$switch_interval>999999] <- NA
data$trial_type <- mapvalues(data$trial_type,from=c("0","1"), to=c("Control Trials","Main Trials"))
# RECODE MAIN AND CONTROL TRAILS OF PROACTIVE BLOCKS, TO ALIGN IN WITH THE LOGIC USED IN THE PAPER
data$trial_type[data$df == 'forced' & data$trial_type == "Main Trials"] <- 'foo'
data$trial_type[data$df == 'forced' & data$trial_type == "Control Trials"] <- 'Main Trials'
data$trial_type[data$df == 'forced' & data$trial_type == "foo"] <- 'Control Trials'

# running preprocessing
data %<>% ddply(.(subj), .fun=findOutliers)
#data %<>%ddply(.(subj,block_no),.fun=fixRT)

# compute sequence of switches and repetitions
data_clean <- data
print(nrow(data_clean))

data_clean <- data_clean[!(data_clean$subject_nr %in% excl),]# exclude bad subjects
print(nrow(data_clean))

data_clean$RT2 <- data_clean$RT
data_clean$RT2[data_clean$resp_saccade>1] <- data_clean$sac_lat_trial[data_clean$resp_saccade>1]
#data_clean$RT2 <- data_clean$sac_lat_trial
print(nrow(data_clean))

#data_clean <- data_clean[data_clean$sac_to_S==as.character(data_clean$fixated_circle),]
#data_clean <- data_clean[data_clean$sacToSelection==1,]
data_clean <- data_clean[data_clean$practice == 'no',]
print(nrow(data_clean))
#data_clean <- data_clean[data_clean$SacContainsBlink == 0,]
print(nrow(data_clean))
data_clean <- data_clean[data_clean$trial_no != 1,]
print(nrow(data_clean))
data_clean <- data_clean[data_clean$color_switch != 'None',]
#data_clean <- data_clean[data_clean$filler_block == 0,]
print(nrow(data_clean))

dataAcc <- data_clean[data_clean$sac_no ==1,]

data_clean <- data_clean[data_clean$sac_no ==data_clean$resp_saccade,]
print(nrow(data_clean))

data_clean <- data_clean[data_clean$sac_to_S==as.character(data_clean$fixatedStim),]
print(nrow(data_clean))

data_clean <- data_clean[data_clean$conflict == 0,]

print(nrow(data_clean))
data_clean <- data_clean[data_clean$RT2 > 100 ,]
print(nrow(data_clean))
data_clean <- data_clean[data_clean$outlier == 0,]
print(nrow(data_clean))
data_clean <- data_clean[data_clean$miss == 0,]
print(nrow(data_clean))
data_clean <- data_clean[data_clean$correct == 1,]
print(nrow(data_clean))
###############
#Calculate Acc
###############

dataAcc %<>% ddply(.(subject_nr,df,color_switch), summarize, Macc = mean(correct))
data_gAcc <- ddply(dataAcc,.(df,color_switch), summarize, Acc = mean(Macc))
#write csv file to run anova on
dataAcc_out <- dataAcc[,c(-5,-6)]
dataAcc_out <- dcast(dataAcc_out, subject_nr ~ df* color_switch, value.var="Macc")
#write.csv(dataAcc_out, file = paste(outDir,"BA5_collapsed_acc.csv",sep=""),row.names=FALSE)
dataAcc_limits <- dataAcc # transform data frame to only contain measurements
# per fixation position
dataAcc_limits <- dcast(dataAcc_limits, subject_nr ~ df*color_switch, value.var="Macc")
dataAcc_limits <- dataAcc_limits[,2:ncol(dataAcc_limits)]
n <- cm.ci(dataAcc_limits)
limits <- aes(ymax = n[[1]][,1]*100, ymin=n[[1]][,2]*100)
#bar plot
p <- ggplot(data_gAcc,aes(x=df, y=Acc*100,fill=color_switch)) +
    geom_errorbar(limits, position=position_dodge(width=0.8),width = 0.3) +
    geom_bar(stat="identity",position=position_dodge(width=0.8),width = 0.7,colour="black")+
    scale_fill_manual(values=c("grey50", "gray90"),name = 'Target Selection', 
     	labels=c("Repetition", "Switch")) +
    scale_x_discrete( labels=c("One Target Available\n(Reactive)","Both Targets Available\n(Proactive)"))+ 
    coord_cartesian(ylim=c(72,105))+
    guides(fill = guide_legend(override.aes = list(colour = NULL))) +
    theme_bw() + xlab('Target Availability\n(Control)') +  ylab('Accuracy (in %)') + 
	theme(axis.title.x=element_text(vjust=-1.5,size=27, family = 'Helvetica'),
		axis.title.y=element_text(vjust=0.3,size=27, family = 'Helvetica'),  
		axis.text.x = element_text(vjust=+.3,size=23, family = 'Helvetica'), 
		axis.text.y = element_text(vjust=+.3,size=23, family = 'Helvetica'), 
		axis.line = element_line(color = 'black'),
		panel.margin = unit(2,'lines'), panel.border = element_blank(),
		panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
		legend.title=element_text(size=27, family = 'Helvetica'),
		legend.position = c(0.28,0.90), 
		legend.text=element_text(size=23, family = 'Helvetica'),
		legend.key = element_rect(size = 2,colour = "white"),
        legend.key.size = unit(2, 'lines'),
        plot.margin = unit(c(0.2,0.2,1,0.5),'cm'))
	p
	ggsave(paste(plotDir,'fMRI_acc_coll.pdf',sep=""))

# analysis with afex: 
AccAOV <- aov_ez("subject_nr", "Macc", dataAcc, within = c("df", "color_switch"),
	anova_table=list(correction = "none", es = "ges"))
contrastTable <- lsmeans(AccAOV, ~df*color_switch)
summary(pairs(contrastTable, adjust="bonferroni"))
####################################################################################
# FIRST ANALYSIS: Rep vs. Switch collapsed over trial type
####################################################################################

costControl_df <- data_clean
# Original analysis
costControl_df %<>% ddply(.(subject_nr, df, color_switch), summarize,
				count = length(RT2), RT= mean(RT2),swi= mean(switch_interval,na.rm=T))
gcostControl_df <- ddply(costControl_df, .(df,color_switch), summarize, 
				RT= mean(RT),count = mean(count),swi = mean(swi,na.rm=T))
#Second level
ggcostControl_df <- ddply(gcostControl_df, .(df,color_switch), summarize, 
				RT= mean(RT),count = mean(count),swi = mean(swi,na.rm=T))

costControl_df <- costControl_df[which(costControl_df$color_switch %in% c(0,1)),]

# compute error bars (according to morey,2008)
costControl_df_limits <- gcostControl_df # transform data frame to only contain measurements
# per fixation position
costControl_df_limits <- dcast(costControl_df_limits, subject_nr ~ df*color_switch, value.var="RT")
costControl_df_limits <- costControl_df_limits[,2:ncol(costControl_df_limits)]
n <- cm.ci(costControl_df_limits)
limits <- aes(ymax = n[[1]][,1], ymin=n[[1]][,2])

# Create csv File for ANOVA
costControl_df <- costControl_df[,c(-4,-6)]
costControl_df_out <- dcast(costControl_df, subject_nr ~ df* color_switch, value.var="RT")
#write.csv(costControl_df_out, file = paste(outDir,"BA5_collapsed_SacLat_v1.csv",sep=""),row.names=FALSE)

#bar plot
breaks <- seq(300,540,by=25)
p <- ggplot(ggcostControl_df,aes(x=df, y=RT,fill=color_switch)) +
    geom_errorbar(limits, position=position_dodge(width=0.8),width = 0.3) +
    geom_bar(stat="identity",position=position_dodge(width=0.8),width = 0.7,colour="black")+
    scale_fill_manual(values=c("grey50", "gray90"),name = 'Target Selection', 
     	labels=c("Repetition", "Switch")) +
    scale_x_discrete( labels=c("One Target Available\n(Reactive)","Both Targets Available\n(Proactive)"))+ 
    scale_y_continuous(breaks=breaks)+
    coord_cartesian(ylim=c(300,540))+
    guides(fill = guide_legend(override.aes = list(colour = NULL))) +
    theme_bw() +xlab('Target Availability\n(Control)') +  ylab('Saccade Latency (in ms)') + 
	theme(axis.title.x=element_text(vjust=-1.5,size=27,face='bold', family = 'Helvetica'),
		axis.title.y=element_text(vjust=0.3,size=27,face='bold', family = 'Helvetica'),  
		axis.text.x = element_text(vjust=+.3,size=23, family = 'Helvetica'), 
		axis.text.y = element_text(vjust=+.3,size=23, family = 'Helvetica'), 
		axis.line = element_line(color = 'black'),
		panel.margin = unit(2,'lines'), panel.border = element_blank(),
		panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
		legend.title=element_text(size=27, family = 'Helvetica'),
		legend.position = c(0.22,0.90), 
		legend.text=element_text(size=23, family = 'Helvetica'),
		legend.key = element_rect(size = 2,colour = "white"),
        legend.key.size = unit(2, 'lines'),
        plot.margin = unit(c(0.2,0.2,1,0.5),'cm'))
	p
#ggsave(paste(plotDir,'BA5_collpased_sacLat.pdf',sep=""),width = 25,unit='cm')
attach(costControl_df_limits)
ttest <- t.test(forced_0,forced_1,paired=TRUE)
cohensD <- cohens_d(forced_0,forced_1)
ttest2 <- t.test(free_0,free_1,paired=TRUE)
cohensD2 <- cohens_d(free_0,free_1)
detach(costControl_df_limits)

costControl_df$subject_nr <- as.factor(costControl_df$subject_nr)
bfBasic2 <- anovaBF(RT~color_switch*df+subject_nr,data= costControl_df, whichRandom="subject_nr",iterations=1e5)
#bfBasic2 <- anovaBF(RT~color_switch*df+subj,data= costControl_df, whichRandom="subj",whichModels='all',iterations=1e5)
samples4 <-	posterior(bfBasic2,4,iterations = 1e5)
nconsistent4 = sum((samples4[, "df:color_switch-forced.&.0"] < samples4[, "df:color_switch-forced.&.1"]) & 
			((samples4[, "df:color_switch-free.&.1"] > samples4[, "df:color_switch-free.&.0"]) | 
			(samples4[, "df:color_switch-free.&.1"] < samples4[, "df:color_switch-free.&.0"])) )

bf_restriction_against_full4 = (nconsistent4 / 1e5) / (1 / 8)

bf_full_against_null = as.vector(bfBasic2)
bf_restriction_against_null4 = bf_restriction_against_full4 * bf_full_against_null[4]

#ANOVA
saclatAOV <- aov_ez("subject_nr", "RT", costControl_df, within = c("df", "color_switch"),
	anova_table=list(correction = "none", es = "ges"))
contrastTable <- lsmeans(saclatAOV, ~df*color_switch)
summary(pairs(contrastTable, adjust="bonferroni"))

####################################################################################
# Second ANALYSIS: Rep vs. Switch across trial type
####################################################################################

costComplete_df <- data_clean

#First level
costComplete_df %<>% ddply(.(subject_nr, trial_type ,df, color_switch), summarize,
				count = length(RT2), RT= mean(RT2),swi= mean(switch_interval,na.rm=T))
#Second level
gcostComplete_df <- ddply(costComplete_df, .(trial_type,df,color_switch), summarize, 
				RT= mean(RT),count = mean(count),swi = mean(swi,na.rm=T))

costComplete_df <- costComplete_df[which(costComplete_df$color_switch %in% c(0,1)),]
costComplete_df$trial_type <- as.factor(costComplete_df$trial_type)
# compute error bars (according to morey,2008)
costComplete_df_limits <- costComplete_df # transform data frame to only contain measurements
# per fixation position
costComplete_df_limits <- dcast(costComplete_df_limits, subject_nr ~ trial_type*df*color_switch, value.var="RT")
costComplete_df_limits <- costComplete_df_limits[,2:ncol(costComplete_df_limits)]
n <- cm.ci(costComplete_df_limits)
limits <- aes(ymax = n[[1]][,1], ymin=n[[1]][,2])

# Create csv File for ANOVA
costComplete_df <- costComplete_df[,c(-5,-7)]
costComplete_df_out <- dcast(costComplete_df, subject_nr ~ trial_type*df* color_switch, value.var="RT")
#write.csv(costComplete_df_out, file = paste(outDir,"BA5_full_SacLat.csv",sep=""),row.names=FALSE)
bfBasic2 <- anovaBF(RT~color_switch*trial_type*df+subject_nr,data= costComplete_df, whichRandom="subj",iterations=1e5)

# bar plot 
p <- ggplot(gcostComplete_df,aes(x=df, y=RT,fill=color_switch)) +
    geom_errorbar(limits, position=position_dodge(width=0.8),width = 0.3) +
    geom_bar(stat="identity", position=position_dodge(width=0.8),width = 0.7, colour="black") +
    scale_fill_manual(values=c("grey50", "gray90"),name = 'Target Selection', 
     	labels=c("Repetition", "Switch")) +
    scale_x_discrete( labels=c("One Target Available\n(Reactive)","Both Targets Available\n(Proactive)"))+ 
    coord_cartesian(ylim=c(350,532))+
    guides(fill = guide_legend(override.aes = list(colour = NULL))) +
    theme_bw() + xlab('Target Availability\n(Control)') +  ylab('Saccade Latency (in ms)') + 
	facet_grid( .~trial_type) + 
	theme(axis.title.x=element_text(vjust=-1.5,size=40, family = 'Helvetica'),
		axis.title.y=element_text(vjust=+1.5,size=40, family = 'Helvetica'),  
		axis.text.x = element_text(vjust=+.3,size=30, family = 'Helvetica'), 
		axis.text.y = element_text(vjust=+.3,size=30, family = 'Helvetica'),  
		axis.line = element_line(color = 'black'),
		plot.margin = unit(c(0.2,0.2,1,0.5),'cm'),
		panel.margin = unit(2,'lines'),panel.border = element_blank(),
		panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
		strip.background = element_rect(color='#FFFFFF' , fill="#FFFFFF"),
		strip.text.x = element_text(size=37, family = 'Helvetica'),
		legend.position = c(0.88,0.70), 
		legend.title=element_text(size=40, family = 'Helvetica'),
		legend.text=element_text(size=30, family = 'Helvetica'),
		legend.key = element_rect(size = 2,colour = "white"),
        legend.key.size = unit(2, 'lines'))
ggsave(paste(plotDir,'BA5_full_sacLat.pdf',sep=""),height = 30, width = 50,unit='cm')

#ANOVA
saclatAOV_comp <- aov_ez("subject_nr", "RT", costComplete_df, within = c("df","trial_type", "color_switch"),
	anova_table=list(correction = "none", es = "ges"))
contrastTable <- lsmeans(saclatAOV_comp, ~df*color_switch*trial_type)
summary(pairs(contrastTable, adjust="bonferroni"))
####################################################################################
# Additional Stats
####################################################################################

# get descriptive stats OF mean (And SD) time between switches
DFSwiInt <- data_clean
DFSwiInt %<>% ddply(.(subject_nr, trial_type,df,color_switch), summarize,
						swi= mean(switch_interval,na.rm=T))
gDFSwiInt <- ddply(DFSwiInt, .(trial_type,df,color_switch), summarize, 
						swi= mean(swi))

# add number of switches
switchRate_df <- data_clean
switchRate_df$noS <- as.numeric(as.character(switchRate_df$no_switch))
switchRate_df %<>% ddply(.(subject_nr,df,block_no), summarize,
						RT= mean(noS,na.rm=T))
gswitchRate_df <- ddply(switchRate_df, .(subject_nr,df), summarize, 
						RT2= mean(RT,na.rm = T), Rr = min(RT,na.rm = T),RTT = max(RT,na.rm = T))
gswitchRate_df2 <- ddply(gswitchRate_df, .(df), summarize, 
						RT4= mean(RT2), Rr = min(RT2),RTT = max(RT2))
ttest <- t.test(gswitchRate_df$RT2[gswitchRate_df$df == 'forced'],gswitchRate_df$RT2[gswitchRate_df$df == 'free'],paired=TRUE)
cohensD <- cohens_d(gswitchRate_df$RT2[gswitchRate_df$df == 'forced'],gswitchRate_df$RT2[gswitchRate_df$df == 'free'])