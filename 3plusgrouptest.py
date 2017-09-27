# Script for running statistical tests on three or more groups of values
# By Robert Silen, robert.silen@iki.fi
#
# Reads cvs file, performs tests, and writes separate output csv file
#
# To run script, write in command prompt or terminal: 
# python 3plusgrouptest.py <name of input csv file>
# Data in input file needs to be in same format as "example.cvs"
#

import sys
import time
import pandas as pd
import numpy as np
from scipy.stats import kruskal
from scipy.stats import friedmanchisquare
from scipy.stats import levene
from scipy.stats import shapiro

# Read data from file and prepare for test
input = 'example.csv'
if sys.argv[1:]:
	input = sys.argv[1]
print("Reading: "+str(input))
df = pd.read_csv(input)
df.set_index('Person',inplace=True)
df = df.T
print('Dataframe size: '+str(df.shape)) 
	
grouped = df[['Group']].groupby('Group')
a = grouped.size().tolist()
len_first = a[0] if a else None
if all(x == len_first for x in a):
	print ('Groups are equal size.')
	equalsize = True
else: 
	print ('Groups are NOT equal size. Friedman test will not be run.')
	equalsize = False
	
# Prepare to capture results
results_nans = pd.DataFrame(columns = ['NaNs'])
results_zeroes = pd.DataFrame(columns = ['Zeroes'])
results_kurt = pd.DataFrame(columns = ['KURT-0', 'KURT-1'])
results_skew = pd.DataFrame(columns = ['SKEW-0', 'SKEW-1'])
results_var = pd.DataFrame(columns = ['VAR-0', 'VAR-1'])
results_shapiro = pd.DataFrame(columns = ['Shapiro Norm-0', 'Shapiro Norm-1'])
results_levene = pd.DataFrame(columns = ['Levene Static', 'Levene P Var'])
results_kruskal = pd.DataFrame(columns = ['Kruskal Static','Kruskal P-Value'])
results_friedman = pd.DataFrame(columns = ['Friedman Static','Friedman P-Value'])

for column in df.ix[:,1:]:
	results_zeroes.loc[column] = sum(df[column].apply(pd.to_numeric) == 0)
	results_nans.loc[column] = sum(df[column].isnull())
	args = []
	for name,group in grouped:
		args.append(df[column].loc[df['Group'] == name].apply(pd.to_numeric))
	for i, element in enumerate(args):
		results_kurt.loc[column,'KURT-'+str(i)] = element.kurt()
		results_skew.loc[column,'SKEW-'+str(i)] = element.skew()
		results_var.loc[column,'VAR-'+str(i)] = element.var()
		results_shapiro.loc[column,'Shapiro Norm-'+str(i)] = shapiro(element)[1]
	if df[column].isnull().values.any():
		print('NaN values found: '+str(column))
	else:
		results_kruskal.loc[column] = (kruskal(args[0],*args[1:]))
		results_levene.loc[column] = (levene(args[0],*args[1:]))
	if equalsize:
		results_friedman.loc[column] = (friedmanchisquare(args[0],*args[1:]))	

df = pd.concat([results_nans, results_zeroes, results_kurt, results_skew, results_var, results_shapiro, results_levene, results_kruskal, results_friedman, df.T], axis=1)


# Write file
if input.endswith('.csv'):
    input = input[:-4]
output = input+'_'+time.strftime("%d-%m-%Y")+".csv"
print("Writing: "+str(output))
df.to_csv(output)   
