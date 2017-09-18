# Script for running statistical tests on two groups of values
# By Robert Silen, robert.silen@iki.fi
#
# Reads cvs file, performs tests, and writes separate output csv file
# Tests run: 
# Mann-Whitney U test for two independent groups of values 
#  (prefered over ttest when samples are not normaly distributed)
# Basic stats on the value groups: variance, skew, kurtosis, etc. 
# Optional: Wilcox test for two dependent groups of values (requires identical sample size)
#
# To run script, write in command prompt or terminal: 
# python 2grouptest.py <name of input csv file>
# Data in input file needs to be in same format as "example.cvs"
#

import sys
import time
import pandas as pd
from scipy.stats import mannwhitneyu
from scipy.stats import wilcoxon
from scipy.stats import shapiro
from scipy.stats import levene

# Read data from file and prepare for test
# Test can be mw, wilcox
test = 'mw'
input = sys.argv[1]
print("Reading data from file: ")
print(input)
df = pd.read_csv(input)
df.set_index('Person',inplace=True)
df = df.T
print('Dataframe size: '+str(df.shape)) 

# Perform Mann-Whitney and related tests
if test=='mw': 
	print("Performing Mann-Whitney and related tests.")
	results_zeroes = pd.DataFrame(columns = ['Zeroes-0','Zeroes-1'])
	results_kurt = pd.DataFrame(columns = ['KURT-0', 'KURT-1'])
	results_skew = pd.DataFrame(columns = ['SKEW-0', 'SKEW-1'])
	results_var = pd.DataFrame(columns = ['VAR-0', 'VAR-1'])
	results_shapiro = pd.DataFrame(columns = ['Shapiro-0 Norm', 'Shapiro-1 Norm'])
	results_levene = pd.DataFrame(columns = ['Levene P Var'])
	results_mw = pd.DataFrame(columns = ['Mann-Whitney P'])
	for column in df.ix[:,1:]:
		groupa = df.ix[:,column].loc[df['Group'] == 'DONOR-0'].apply(pd.to_numeric)
		groupb = df.ix[:,column].loc[df['Group'] == 'DONOR-1'].apply(pd.to_numeric)
		results_zeroes.loc[column,'Zeroes-0'] = sum(groupa == 0)
		results_zeroes.loc[column,'Zeroes-1'] = sum(groupb == 0)
		results_kurt.loc[column,'KURT-0'] = groupa.kurt()
		results_kurt.loc[column,'KURT-1'] = groupb.kurt()
		results_shapiro.loc[column] = shapiro(groupa)[1]
		results_shapiro.loc[column] = shapiro(groupb)[1]	
		results_skew.loc[column,'SKEW-0'] = groupa.skew()
		results_skew.loc[column,'SKEW-1'] = groupb.skew()
		results_levene.loc[column] = levene(groupa, groupb)[1]
		results_var.loc[column,'VAR-0'] = groupa.var()
		results_var.loc[column,'VAR-1'] = groupb.var()
		results_mw.loc[column] =  mannwhitneyu(groupa, groupb,alternative='two-sided')[1]
	df = pd.concat([results_zeroes, results_kurt, results_skew, results_var, results_shapiro, results_levene, results_mw, df.T], axis=1)
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
	print("Writing data to file:")
	print(output)
	df.to_csv(output)   
else:
	print("Test not completed")
