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
import glob
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
import sys
import threading

# Progress Bar (for when statistical analysis is being done) 
class ProgressBar(threading.Thread):
     """
     In a separate thread, print dots to the screen until terminated.
     """
     def __init__(self):
         threading.Thread.__init__(self)
         self.event = threading.Event()
     def run(self):
         event = self.event # make local
         sys.stdout.write("Working: ")
         while not event.is_set():
             sys.stdout.write(".")
             sys.stdout.flush()
             event.wait(1) # pause for 1 second
         sys.stdout.write("\n")
     def stop(self):
         self.event.set()

# Function that makes statistical calculations on dataframe
# Takes and returns dataframe
def Calculate(df):
	print('Dataframe columns, rows: '+str(df.shape)) 
	# Check amount of groups
	grouped = df.groupby(['Source','Group'])
	groupamount = 0
	groupamount = len(grouped)
	print ('Amount of groups: '+str(groupamount))

	# Check if equal size groups or not
	equalsize = False
	a = grouped.size().tolist()
	len_first = a[0] if a else None
	if all(x == len_first for x in a):
		equalsize = True
		print ('Groups are equal size: '+str(a))
	else: 
		print ('Groups are NOT equal size: '+str(a))

	# Start the Progress Bar and capture errors
	try: 
		progress_bar = ProgressBar()
		progress_bar.start()

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
		for column in df.ix[:,2:]:
			firstrun = True
			results_zeroes.loc[column,'Zeroes'] = sum(df[column].astype(float) == 0)
			explanations.loc['Group','Zeroes'] = 'Possible errors'
			results_nans.loc[column,'NaNs'] = sum(df[column].isnull())
			explanations.loc['Group','NaNs'] = 'Not A Number, possible errors'
			args = []
			names = []
			for name,group in grouped:
				id = str(name[0])+"-"+str(name[1])
				results_medians.loc[column,'Median - '+id] = group[column].astype(float).median()
				results_kurt.loc[column,'Kurtosis - '+id] =group[column].astype(float).kurt()
				if firstrun==True: explanations.loc['Group','Kurtosis - '+id] = 'Not normal when <-3 or >3'
				results_skew.loc[column,'Skewness - '+id] = group[column].astype(float).skew()
				if firstrun==True: explanations.loc['Group','Skewness - '+id] = 'Not normal when <-0.8 or >0.8'
				if runshapiro==True: 
					results_shapiro.loc[column,'Shapiro Norm - '+id] = shapiro(group[column].astype(float))[1]
				if firstrun==True: explanations.loc['Group','Shapiro Norm - '+id] = 'Not normal when <0.05'
				results_var.loc[column,'Variance - '+id] = group[column].astype(float).var()
				if firstrun==True: explanations.loc['Group','Variance - '+id] = 'The spread from the average'
				args.append(group[column].astype(float))
			results.loc[column,'Levene P-Value'] = levene(args[0],*args[1:])[0]
			if firstrun==True: explanations.loc['Group','Levene P-Value'] = 'Variance is different when <0.05' 
			results.loc[column,'T-Test Ind. P-value'] = (ttest_ind(args[0],*args[1:])[1]) if groupamount==2 else 'NaN'
			if firstrun==True: explanations.loc['Group','T-Test Ind. P-value'] = '2 groups independent. Asumes normal dist. Criteria <0.05'
			results.loc[column,'Mann-Whitney P-value'] = (mannwhitneyu(args[0],*args[1:])[1]) if groupamount==2 else 'NaN'
			if firstrun==True: explanations.loc['Group','Mann-Whitney P-value'] = '2 groups independent non-parametric. Criteria <0.05'
			results.loc[column,'T-Test Rel. P-value'] = (ttest_rel(args[0],*args[1:])[1]) if groupamount==2 and equalsize else 'NaN'
			if firstrun==True: explanations.loc['Group','T-Test Rel. P-value'] = '2 groups dependent. Asumes normal dist. and equal size. Criteria <0.05'
			results.loc[column,'Wilcoxon P-value'] = (wilcoxon(args[0],*args[1:])[1]) if groupamount==2 and equalsize else 'NaN'
			if firstrun==True: explanations.loc['Group','Wilcoxon P-value'] = '2 groups dependent non-parametric. Asumes equal size. Criteria <0.05'
			results.loc[column,'ANOVA One-Way P-value'] = (f_oneway(args[0],*args[1:])[1]) if groupamount>1 else 'NaN'
			if firstrun==True: explanations.loc['Group','ANOVA One-Way P-value'] = '3 groups independent. Asumes normal dist. Criteria <0.05'
			results.loc[column,'Kruskal P-value'] = (kruskal(args[0],*args[1:])[0]) if groupamount>1 else 'NaN'
			if firstrun==True: explanations.loc['Group','Kruskal P-value'] = '2+ groups independent non-parametric. Criteria <0.05'
			results.loc[column,'Friedman P-value'] = (friedmanchisquare(args[0],*args[1:])[1]) if groupamount>2 and equalsize else 'NaN'
			if firstrun==True: explanations.loc['Group','Friedman P-value'] = '3 groups dependent non-parametric. Asumes equal size. Criteria <0.05'
			firstrun = False

		# Explanations of each test
		summary_zeroes = results_zeroes.copy().astype(int)
		summary_zeroes.loc['Criteria Count'] = results_zeroes[results_zeroes != 0].count().apply('{:d}'.format)
		summary_zeroes.loc['Total Count'] = len(results_zeroes)

		summary_nans = results_nans.copy().astype(int)
		summary_nans.loc['Criteria Count'] = results_nans[results_nans != 0].count().apply('{:d}'.format)
		summary_nans.loc['Total Count'] = len(results_nans)

		summary_kurt = results_kurt.copy()
		summary_kurt.loc['Criteria Count'] =  results_kurt[(results_kurt < -3) | (results_kurt > 3)].count().apply('{:d}'.format)
		summary_kurt.loc['Total Count'] = len(results_kurt)
		summary_kurt.loc['Percentage'] = (results_kurt[(results_kurt < -3) | (results_kurt > 3)].count() / len(results_kurt)).apply('{:.0%}'.format)

		summary_skew = results_skew.copy()
		summary_skew.loc['Criteria Count'] = results_skew[(results_skew < -0.8) | (results_skew > 0.8)].count().apply('{:d}'.format)
		summary_skew.loc['Total Count'] =  len(results_skew)
		summary_skew.loc['Percentage'] =  (results_skew[(results_skew < -0.8) | (results_skew > 0.8)].count() / len(results_skew)).apply('{:.0%}'.format)

		summary_shapiro = results_shapiro.copy()
		if runshapiro==True: summary_shapiro.loc['Criteria Count'] = results_shapiro[(results_shapiro < 0.05)].count().apply('{:d}'.format)
		if runshapiro==True: summary_shapiro.loc['Total Count'] =  len(results_shapiro)
		if runshapiro==True: summary_shapiro.loc['Percentage'] = (results_shapiro[(results_shapiro < 0.05)].count() / len(results_shapiro)).apply('{:.0%}'.format)

		summary = results.copy()
		summary.loc['Criteria Count'] =  results[(results < 0.05)].count().apply('{:d}'.format)
		summary.loc['Total Count'] =  len(results)
		summary.loc['Percentage'] = (results[(results < 0.05)].count() / len(results)).apply('{:.0%}'.format)

		df = pd.concat([
			summary_zeroes, 
			summary_nans, 
			results_medians, 
			summary_kurt,
			summary_skew, 
			summary_shapiro,
			results_var, 
			summary, 
			df.T
			], axis=1)
		df = pd.concat([df.loc[['Total Count'],:], df.drop('Total Count', axis=0)], axis=0)	
		df = pd.concat([df.loc[['Criteria Count'],:], df.drop('Criteria Count', axis=0)], axis=0)
		df = pd.concat([df.loc[['Percentage'],:], df.drop('Percentage', axis=0)], axis=0)
		df = pd.concat([df.loc[['Group'],:], df.drop('Group', axis=0)], axis=0)
		df = pd.concat([df.loc[['Source'],:], df.drop('Source', axis=0)], axis=0)

		df.update(explanations)

		# End progress bar, also if error
		progress_bar.stop()
		progress_bar.join()
		return df
	except: 
		progress_bar.stop()
		progress_bar.join()
		print "\nUnexpected error:", sys.exc_info()[0]
		exit()

# Individual calculations: loop through all files listed in array inputfiles
def Individual(data, filenames):
	print "Handling as individual files"
	for j, element in enumerate(data):
		print "\nCalculating: "+filenames[j]
		df = Calculate(element)
		# Write file
		if filenames[j].endswith('.csv'):
			filenames[j] = filenames[j][:-4]
		output = filenames[j]+'_results_'+time.strftime("%d-%m-%Y")+".csv"
		print("Writing: "+str(output))
		df.to_csv(output)


# TimeSeries calculations: combine all files listed in array inputfiles
def TimeSeries(data, filenames):
	print "Combining all groups from files, e.g. for timeseries"
	# merge dataframes, change cells to numeric, not objects
	df = pd.concat(data, axis=0, join='inner')
	df = pd.concat([df.ix[:,:2], df.ix[:,2:].apply(pd.to_numeric)], axis=1)
	# move groups and timeseries to first columns
	cols = list(df)
	cols.insert(0, cols.pop(cols.index('Group')))
	cols.insert(0, cols.pop(cols.index('Source')))
	df = df.ix[:, cols]
	
	df_temp = Calculate(df)
	
	# Write file
	if filenames[0].endswith('.csv'):
		filenames[0] = filenames[0][:-4]
	output = filenames[0]+'_ts-results_'+time.strftime("%d-%m-%Y")+".csv"
	print("Writing: "+str(output))
	df_temp.to_csv(output)

	# plotting
	print "Plotting figures"
	for column in df.ix[:,2:]:
		fig, ax = plt.subplots()
		labels = []
		for key, grp in df.groupby(['Source', 'Group'])[[column]].median().groupby(['Source']):
			ax = grp.reset_index().plot(ax=ax, x='Group', y=column, kind='line', title=column)
			labels.append(key)
		lines, _ = ax.get_legend_handles_labels()
		ax.legend(lines, labels, loc='best')
		if not os.path.exists("fig"):
			print "Creating folder fig"
			os.makedirs("fig")
		print 'Writing: fig/'+column+'.png'
		plt.savefig('fig/'+column+'.png')
		plt.clf()
		plt.close()

# Create dataframe array that will be passed to TimeSeries or Individual function
if len(sys.argv) < 2: 
	sys.argv.append('example.csv')
data = []
filenames = []
runshapiro = True
runnormality = True
timeseries = False

print "\nInput files:" 
for j, element in enumerate(sys.argv[1:]):
	if element == "-noshapiro":
		runshapiro = False
	if element == "-timeseries":
		timeseries = True
	else: 
		for k, file in enumerate(glob.glob(element)):
			print file
			filenames.append(file)
			data.append(pd.read_csv(element))
			data[-1].set_index('Person',inplace=True)
			input = element
			if input.endswith('.csv'):
				input = input[:-4]
			data[-1] = data[-1].T
			data[-1].insert(loc=1, column='Source', value=input)
if timeseries: 
	TimeSeries(data, filenames)
else: 
	Individual(data, filenames)
