# Script for running statistical tests on two groups of values
# By Robert Silén, robert.silen@iki.fi
#
# Reads cvs file, performs tests, and writes separate output csv file
# Tests run: 
# Mann-Whitney U test for two independent groups of values 
#  (prefered over ttest when samples are not normaly distributed)
# Basic stats on the value groups: variance, skew, kurtosis, etc. 
# Optional: Wilcox test for two dependent groups of values (requires identical sample size)
#
# To run script, write in command prompt or terminal: 
# python 2pairedtest.py <name of input csv file>
# Data in input file needs to be in same format as "example.cvs"
# 
# Version: 0.11
# Released: 14.9.2017
# Release note: Added count of zeroes
#

import sys
import time
import pandas as pd
from scipy.stats import mannwhitneyu
from scipy.stats import wilcoxon
#from scipy.stats import levene
#from scipy.stats import skewtest

# Read data from file and prepare for test
# Test can be mw, wilcox
test = 'mw'
input = sys.argv[1]
print("Reading data from excel file: "+input)
df = pd.read_csv(input)
df.set_index('Person',inplace=True)
df = df.T
print('Dataframe size: '+str(df.shape)) 

# Perform MWU Test
if test=='mw': 
	results_var = pd.DataFrame(columns = ['VAR-0', 'VAR-1'])
	results_skew = pd.DataFrame(columns = ['SKEW-0', 'SKEW-1', 'SkewTest-0', 'SkewTest-1'])
	results_kurt = pd.DataFrame(columns = ['KURT-0', 'KURT-1'])
	results_zeroes = pd.DataFrame(columns = ['Zeroes-0','Zeroes-1'])
	results_mw = pd.DataFrame(columns = ['MW Z','MW P'])
	print("Performing Mann-Whitney U Test.")
	for column in df.ix[:,1:]:
		groupa = df.ix[:,column].loc[df['Group'] == 'DONOR-0'].apply(pd.to_numeric)
		groupb = df.ix[:,column].loc[df['Group'] == 'DONOR-1'].apply(pd.to_numeric)
		results_var.loc[column,'VAR-0'] = groupa.var()
		results_var.loc[column,'VAR-1'] = groupb.var()
		results_skew.loc[column,'SKEW-0'] = groupa.skew()
		results_skew.loc[column,'SKEW-1'] = groupb.skew()
		results_skew.loc[column,'SkewTest-0'] = skewtest(groupa)[1]	
		results_skew.loc[column,'SkewTest-1'] = skewtest(groupb)[1]
		results_kurt.loc[column,'KURT-0'] = groupa.kurt()
		results_kurt.loc[column,'KURT-1'] = groupb.kurt()
		results_zeroes.loc[column,'Zeroes-0'] = sum(df.ix[:,column].loc[df['Group'] == 'DONOR-0'].apply(pd.to_numeric) == 0)
		results_zeroes.loc[column,'Zeroes-1'] = sum(df.ix[:,column].loc[df['Group'] == 'DONOR-1'].apply(pd.to_numeric) == 0)
		results_mw.loc[column] =  mannwhitneyu(groupa, groupb)
	df = pd.concat([results_skew, results_kurt, results_var, results_zeroes, results_mw, df.T], axis=1)
	success = True

# Perform Wilcox Test	
if test=='wilcox':
        if df.isnull().values.any():
        	print('Data contains Nulls')
        	exit()
	results = pd.DataFrame(columns = ['Wilcox Z-Value','Wilcox P-Value'])
	print("Performing Wilcox Test")
	for column in df.ix[:,1:]:
		groupa = df.ix[:,column].loc[df['Group'] == 'DONOR-0'].apply(pd.to_numeric)
		groupb = df.ix[:,column].loc[df['Group'] == 'DONOR-1'].apply(pd.to_numeric)
		results.loc[column] =  wilcoxon(groupa, groupb)
	df = pd.concat([results, df.T], axis=1)
	success = True

# Write file
if success: 
	output = input+'-'+test+'-'+time.strftime("%d-%m-%Y")+".csv"
	print("Writing data to "+output)
	df.to_csv(output)       
else:
	print("Test not completed")
