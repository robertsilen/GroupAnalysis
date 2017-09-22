# Script for running statistical tests on three or more groups of values
# By Robert Silen, robert.silen@iki.fi
#
# Reads cvs file, performs tests, and writes separate output csv file
# Tests run: 
# Kruskal-Wallis H Test for three or more independent groups of values 
#  (prefered over "one-way ANOVA on ranks" when samples are not normaly distributed)
# Basic stats on the value groups: variance, skew, kurtosis, etc. 
#
# To run script, write in command prompt or terminal: 
# python 3plusgrouptest.py <name of input csv file>
# Data in input file needs to be in same format as "example.cvs"
#

import sys
import time
import pandas as pd
from scipy.stats import kruskal
success = False

# Read data from file and prepare for test
test = 'kruskal'
input = sys.argv[1]
print("Reading data from file: ")
print(input)
df = pd.read_csv(input)
df.set_index('Person',inplace=True)
df = df.T
print('Dataframe size: '+str(df.shape)) 

# Perform Kruskal and related tests
if test=='kruskal': 
	print("Performing Kruskal and related tests.")
	results_zeroes = pd.DataFrame(columns = ['Zeroes'])
	results_kruskal = pd.DataFrame(columns = ['Kruskal Static','Kruskal P-Value'])
	
	grouped = df[['Group']].groupby('Group')
	for column in df.ix[:,1:]:
		args = []
		for name,group in grouped:
			args.append(df[column].loc[df['Group'] == name].apply(pd.to_numeric))
		results_kruskal.loc[column] = (kruskal(args[0],*args[1:]))
		results_zeroes.loc[column] = sum(df[column].apply(pd.to_numeric) == 0)
	df = pd.concat([results_zeroes, results_kruskal, df.T], axis=1)
	success = True

# Write file
if success: 
	output = input+'-'+test+'-'+time.strftime("%d-%m-%Y")+".csv"
	print("Writing data to file:")
	print(output)
	df.to_csv(output)   
else:
	print("Test not completed")
