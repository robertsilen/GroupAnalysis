# Script for running statistical tests in batch
# By Robert Silen, robert.silen@iki.fi
#
# Reads cvs file, performs tests, and writes separate output csv file
#
# To run script, write in command prompt or terminal: 
# python groupanalysis.py <name of input csv file>
# Data in input file needs to be in same format as "example.cvs"
#
# Script outputs a file with statistical values for each input file

import sys
import time
import os.path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import shapiro
from scipy.stats import levene
from scipy.stats import f_oneway
from scipy.stats import ttest_ind
from scipy.stats import mannwhitneyu
from scipy.stats import ttest_rel
from scipy.stats import wilcoxon
from scipy.stats import kruskal
from scipy.stats import friedmanchisquare

# Read data from file and prepare for test
if len(sys.argv) < 2: 
	sys.argv.append('example.csv')

timeseries_values = pd.DataFrame()
timeseries_medians = pd.DataFrame()
timeseries_results = pd.DataFrame()	

for j, element in enumerate(sys.argv[1:]):
	input = element
	
	print("Reading: "+str(input))
	df = pd.read_csv(input)
	
	if input.endswith('.csv'):
		input = input[:-4]
	
	df.set_index('Person',inplace=True)
	timeseries_values = pd.concat([df, timeseries_values], axis=1)
	
	df = df.T
	print('Dataframe columns, rows: '+str(df.shape)) 

	grouped = df[['Group']].groupby('Group')
	groupamount = 0
	groupamount = len(grouped)
	print ('Amount of groups: '+str(groupamount))
	
	equalsize = False
	a = grouped.size().tolist()
	len_first = a[0] if a else None
	if all(x == len_first for x in a):
		equalsize = True
		print ('Groups are equal size: '+str(a))
	else: 
		print ('Groups are NOT equal size: '+str(a))

	# Prepare to capture results
	explanations = pd.DataFrame()
	results_zeroes = pd.DataFrame()
	results_nans = pd.DataFrame()
	results_medians = pd.DataFrame()
	results_kurt = pd.DataFrame()
	results_skew = pd.DataFrame()
	results_shapiro = pd.DataFrame()
	results_var = pd.DataFrame()
	results_levene = pd.DataFrame()
	results = pd.DataFrame()

	for column in df.ix[:,1:]:
		firstrun = True
		results_zeroes.loc[column,'Zeroes'] = pd.to_numeric(sum(df[column] == 0), downcast='integer')
		explanations.loc['Group','Zeroes'] = 'Possible errors'
		results_nans.loc[column,'NaNs'] = sum(df[column].isnull())
		explanations.loc['Group','NaNs'] = 'Not A Number, possible errors'
		args = []
		names = []
		for name,group in grouped:
			args.append(df[column].loc[df['Group'] == name].apply(pd.to_numeric))
			names.append(name)
		for i, element in enumerate(args):
			results_medians.loc[column,'Median - '+names[i]] = element.median()
			timeseries_medians.loc[column,'Median - '+input+'-'+names[i]] = element.median()
			results_kurt.loc[column,'Kurtosis - '+names[i]] = element.kurt()
			if firstrun==True: explanations.loc['Group','Kurtosis - '+names[i]] = '-3 to 3 is normal'
			results_skew.loc[column,'Skewness - '+names[i]] = element.skew()
			if firstrun==True: explanations.loc['Group','Skewness - '+names[i]] = '-0.8 to 0.8 is normal'
			results_shapiro.loc[column,'Shapiro Norm - '+names[i]] = shapiro(element)[1]
			if firstrun==True: explanations.loc['Group','Shapiro Norm - '+names[i]] = 'When < 0.05, the sample deviates from normality'
			results_var.loc[column,'Variance - '+names[i]] = element.var()
			if firstrun==True: explanations.loc['Group','Variance - '+names[i]] = 'How far values are spread out from the average'
		results_levene.loc[column,'Levene P-Value'] = (levene(args[0],*args[1:])[0])
		if firstrun==True: explanations.loc['Group','Levene P-Value'] = 'When <.05 the variability is equal.' 
		results.loc[column,'ANOVA One-Way P-value'] = (f_oneway(args[0],*args[1:])[1]) if groupamount>1 else 'NaN'
		if firstrun==True: explanations.loc['Group','ANOVA One-Way P-value'] = 'When <.05 there is a statistical significant difference'
		results.loc[column,'T-Test Ind. P-value'] = (ttest_ind(args[0],*args[1:])[1]) if groupamount==2 else 'NaN'
		if firstrun==True: explanations.loc['Group','T-Test Ind. P-value'] = 'When <.05 there is a statistical significant difference'
		results.loc[column,'Mann-Whitney P-value'] = (mannwhitneyu(args[0],*args[1:])[1]) if groupamount==2 else 'NaN'
		if firstrun==True: explanations.loc['Group','Mann-Whitney P-value'] = 'When <.05 there is a statistical significant differencs'
		results.loc[column,'T-Test Rel. P-value'] = (ttest_rel(args[0],*args[1:])[1]) if groupamount==2 and equalsize else 'NaN'
		if firstrun==True: explanations.loc['Group','T-Test Rel. P-value'] = 'When <.05 there is a statistical significant differences'
		results.loc[column,'Wilcoxon P-value'] = (wilcoxon(args[0],*args[1:])[1]) if groupamount==2 and equalsize else 'NaN'
		if firstrun==True: explanations.loc['Group','Wilcoxon P-value'] = 'When <.05 there is a statistical significant difference'
		results.loc[column,'Kruskal P-value'] = (kruskal(args[0],*args[1:])[0]) if groupamount>1 else 'NaN'
		if firstrun==True: explanations.loc['Group','Kruskal P-value'] = 'When <.05 there is a statistical significant differences'
		results.loc[column,'Friedman P-value'] = (friedmanchisquare(args[0],*args[1:])[1]) if groupamount>2 and equalsize else 'NaN'
		if firstrun==True: explanations.loc['Group','Friedman P-value'] = 'When <.05 there is a statistical significant difference'
		firstrun = False

	df = pd.concat([
			results_zeroes, 
			results_nans, 
			results_medians, 
			results_kurt, 
			results_skew, 
			results_shapiro,
			results_var, 
			results_levene, 
			results, 
			df.T
			], axis=1)
	df = pd.concat([df.loc[['Group'],:], df.drop('Group', axis=0)], axis=0)
	
	df.update(explanations)

	# Write file
	output = input+'_results_'+time.strftime("%d-%m-%Y")+".csv"
	print("Writing: "+str(output))
	df.to_csv(output)

timeseries_results = pd.concat([timeseries_medians, timeseries_values], axis=1)
timeseries_results = pd.concat([timeseries_results.loc[['Group'],:], timeseries_results.drop('Group', axis=0)], axis=0)

output = 'results'+time.strftime("-%d-%m-%Y")+".csv"
print("Writing: "+str(output))
timeseries_results.to_csv(output)
