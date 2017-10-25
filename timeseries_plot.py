import sys
import pandas as pd   
import matplotlib.pyplot as plt  

# load all input files into array of dataframes
data = []
for j, element in enumerate(sys.argv[1:]):
	data.append(pd.read_csv(element))
	data[j].set_index('Person',inplace=True)
	input = element
	if input.endswith('.csv'):
		input = input[:-4]
	data[j] = data[j].T
	data[j].insert(loc=1, column='TimeSeries', value=input)

# merge dataframes, change cells to numeric, not objects
df = pd.concat(data, axis=0, join='inner')
df = pd.concat([df.ix[:,:2], df.ix[:,2:].apply(pd.to_numeric)], axis=1)
df['Group'] = df['Group'].astype(int)

# move groups and timeseries to first columns
cols = list(df)
cols.insert(0, cols.pop(cols.index('Group')))
cols.insert(0, cols.pop(cols.index('TimeSeries')))
df = df.ix[:, cols]

# plotting
for column in df.ix[:,2:]:
	fig, ax = plt.subplots()
	labels = []
	for key, grp in df.groupby(['TimeSeries', 'Group'])[[column]].median().groupby(['TimeSeries']):
		ax = grp.reset_index().plot(ax=ax, x='Group', y=column, xticks=grp.reset_index()['Group'], kind='line', title=column)
		labels.append(key)
	lines, _ = ax.get_legend_handles_labels()
	ax.legend(lines, labels, loc='best')
	plt.savefig('fig/'+column+'.png')
	plt.clf()
	
df.to_csv('test.csv')
